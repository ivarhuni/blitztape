import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time
from urllib.parse import urljoin, urlparse
import subprocess
import sys

class RUVAdvancedScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.base_url = "https://www.ruv.is"
        self.episodes = []
        
    def get_series_episodes(self, series_url):
        """Get all episodes from a series page"""
        try:
            response = self.session.get(series_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            episodes = []
            
            # Look for episode list - RÚV might have a specific structure
            # Try to find episode containers
            episode_containers = soup.find_all(['div', 'li', 'article'], class_=re.compile(r'episode|video|item'))
            
            if not episode_containers:
                # Try alternative selectors
                episode_containers = soup.find_all('a', href=re.compile(r'/spila/'))
            
            for container in episode_containers:
                # Find the link
                link = container.find('a') if container.name != 'a' else container
                if not link:
                    continue
                    
                href = link.get('href')
                if not href:
                    continue
                
                # Get title
                title = link.get_text(strip=True)
                if not title:
                    # Try to find title in child elements
                    title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                
                if title and href:
                    full_url = urljoin(self.base_url, href)
                    episodes.append({
                        'url': full_url,
                        'title': title
                    })
            
            # If no episodes found, try to extract from the current page
            if not episodes:
                title = soup.find('h1')
                if title:
                    episodes.append({
                        'url': series_url,
                        'title': title.get_text(strip=True)
                    })
            
            return episodes
            
        except Exception as e:
            print(f"Error getting series episodes: {e}")
            return []
    
    def extract_video_data(self, episode_url):
        """Extract video data from an episode page"""
        try:
            response = self.session.get(episode_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic info
            title = soup.find('h1')
            title = title.get_text(strip=True) if title else 'Unknown Title'
            
            video_info = {
                'title': title,
                'url': episode_url,
                'video_url': None,
                'description': '',
                'duration': '',
                'air_date': ''
            }
            
            # Extract description
            desc_elem = soup.find('meta', {'name': 'description'})
            if desc_elem:
                video_info['description'] = desc_elem.get('content', '')
            
            # Look for video player data in JavaScript
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for RÚV-specific video data patterns
                    patterns = [
                        r'"videoUrl"\s*:\s*"([^"]+)"',
                        r'"src"\s*:\s*"([^"]+\.mp4[^"]*)"',
                        r'"url"\s*:\s*"([^"]+\.mp4[^"]*)"',
                        r'"streamUrl"\s*:\s*"([^"]+)"',
                        r'"mediaUrl"\s*:\s*"([^"]+)"',
                        r'https?://[^\s"<>]+\.mp4[^\s"<>]*',
                        r'https?://[^\s"<>]+\.m3u8[^\s"<>]*'
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, script.string)
                        if matches:
                            video_info['video_url'] = matches[0]
                            break
                
                if video_info['video_url']:
                    break
            
            # If no video URL found in scripts, try other methods
            if not video_info['video_url']:
                # Look for video tags
                video_tags = soup.find_all('video')
                for video in video_tags:
                    src = video.get('src')
                    if src:
                        video_info['video_url'] = urljoin(self.base_url, src)
                        break
                
                # Look for source tags
                if not video_info['video_url']:
                    source_tags = soup.find_all('source')
                    for source in source_tags:
                        src = source.get('src')
                        if src:
                            video_info['video_url'] = urljoin(self.base_url, src)
                            break
                
                # Look for iframe players
                if not video_info['video_url']:
                    iframes = soup.find_all('iframe')
                    for iframe in iframes:
                        src = iframe.get('src')
                        if src and ('player' in src or 'video' in src):
                            video_info['video_url'] = src
                            break
            
            return video_info
            
        except Exception as e:
            print(f"Error extracting video data from {episode_url}: {e}")
            return None
    
    def download_with_yt_dlp(self, video_info, output_dir="downloads"):
        """Download video using yt-dlp"""
        if not video_info.get('url'):
            print(f"No URL found for: {video_info['title']}")
            return False
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Clean filename
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', video_info['title'])
        output_file = os.path.join(output_dir, f"{safe_title}.%(ext)s")
        
        try:
            cmd = [
                'yt-dlp',
                '--output', output_file,
                '--format', 'best',
                '--write-description',
                '--write-info-json',
                '--no-check-certificates',
                video_info['url']
            ]
            
            print(f"Downloading: {video_info['title']}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✓ Successfully downloaded: {video_info['title']}")
                return True
            else:
                print(f"✗ yt-dlp failed for {video_info['title']}")
                print(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error downloading {video_info['title']}: {e}")
            return False
    
    def scrape_series(self, series_url, download_videos=True):
        """Main method to scrape an entire series"""
        print(f"Starting to scrape series from: {series_url}")
        print("="*60)
        
        # Get all episode links
        episodes = self.get_series_episodes(series_url)
        print(f"Found {len(episodes)} episodes")
        
        if not episodes:
            print("No episodes found. Trying to scrape the single page...")
            video_info = self.extract_video_data(series_url)
            if video_info:
                episodes = [{'url': series_url, 'title': video_info['title']}]
        
        # Process each episode
        for i, episode in enumerate(episodes, 1):
            print(f"\n[{i}/{len(episodes)}] Processing: {episode['title']}")
            print("-" * 40)
            
            video_info = self.extract_video_data(episode['url'])
            if video_info:
                self.episodes.append(video_info)
                print(f"Title: {video_info['title']}")
                print(f"URL: {video_info['url']}")
                if video_info.get('video_url'):
                    print(f"Video URL: {video_info['video_url']}")
                if video_info.get('description'):
                    print(f"Description: {video_info['description'][:100]}...")
                
                if download_videos:
                    success = self.download_with_yt_dlp(video_info)
                    if not success:
                        print("Download failed, but continuing with other episodes...")
                
                # Be respectful to the server
                time.sleep(3)
            else:
                print(f"Failed to extract video info for: {episode['title']}")
        
        # Save episode information
        with open('episodes.json', 'w', encoding='utf-8') as f:
            json.dump(self.episodes, f, indent=2, ensure_ascii=False)
        
        print(f"\n" + "="*60)
        print(f"Scraping completed! Found {len(self.episodes)} episodes.")
        print("Episode information saved to episodes.json")
        
        return self.episodes

def main():
    scraper = RUVAdvancedScraper()
    
    # The series URL
    series_url = "https://www.ruv.is/sjonvarp/spila/sammi-brunavordur-x/37768/b85s4f"
    
    # Scrape the series
    episodes = scraper.scrape_series(series_url, download_videos=True)
    
    # Print final summary
    print("\n" + "="*60)
    print("FINAL EPISODE SUMMARY")
    print("="*60)
    for i, episode in enumerate(episodes, 1):
        print(f"{i}. {episode['title']}")
        if episode.get('video_url'):
            print(f"   Video URL: {episode['video_url']}")
        print()

if __name__ == "__main__":
    main() 