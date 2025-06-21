import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time
from urllib.parse import urljoin, urlparse
import subprocess
import sys

class RUVImprovedScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'is-IS,is;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.base_url = "https://www.ruv.is"
        self.episodes = []
        
    def get_all_episodes(self, series_url):
        """Get all episodes from a series page by analyzing the page structure"""
        try:
            response = self.session.get(series_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            episodes = []
            
            # Method 1: Look for episode list in the page
            # RÚV might have a specific episode list structure
            episode_sections = soup.find_all(['div', 'section', 'ul'], class_=re.compile(r'episode|video|list|item'))
            
            for section in episode_sections:
                links = section.find_all('a', href=True)
                for link in links:
                    href = link.get('href')
                    if href and '/spila/' in href:
                        title = link.get_text(strip=True)
                        if title:
                            full_url = urljoin(self.base_url, href)
                            episodes.append({
                                'url': full_url,
                                'title': title
                            })
            
            # Method 2: Look for all links containing the series ID
            if not episodes:
                series_id = series_url.split('/')[-1]  # Get the last part of URL
                all_links = soup.find_all('a', href=re.compile(series_id))
                
                for link in all_links:
                    href = link.get('href')
                    title = link.get_text(strip=True)
                    if href and title:
                        full_url = urljoin(self.base_url, href)
                        episodes.append({
                            'url': full_url,
                            'title': title
                        })
            
            # Method 3: Look for navigation or pagination that might contain episode links
            if not episodes:
                nav_elements = soup.find_all(['nav', 'div'], class_=re.compile(r'nav|pagination|episode'))
                for nav in nav_elements:
                    links = nav.find_all('a', href=True)
                    for link in links:
                        href = link.get('href')
                        if href and '/spila/' in href:
                            title = link.get_text(strip=True)
                            if title:
                                full_url = urljoin(self.base_url, href)
                                episodes.append({
                                    'url': full_url,
                                    'title': title
                                })
            
            # Method 4: If no episodes found, treat the current page as a single episode
            if not episodes:
                # Try to extract title from the current page
                title_elem = soup.find(['h1', 'h2', 'title'])
                title = title_elem.get_text(strip=True) if title_elem else "Sammi brunavörður X"
                
                episodes.append({
                    'url': series_url,
                    'title': title
                })
            
            # Remove duplicates
            unique_episodes = []
            seen_urls = set()
            for episode in episodes:
                if episode['url'] not in seen_urls:
                    unique_episodes.append(episode)
                    seen_urls.add(episode['url'])
            
            return unique_episodes
            
        except Exception as e:
            print(f"Error getting episodes: {e}")
            return []
    
    def extract_video_data(self, episode_url):
        """Extract video data from an episode page"""
        try:
            response = self.session.get(episode_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title - try multiple methods
            title = None
            
            # Method 1: Look for h1 tag
            h1_elem = soup.find('h1')
            if h1_elem:
                title = h1_elem.get_text(strip=True)
            
            # Method 2: Look for title tag
            if not title:
                title_elem = soup.find('title')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    # Clean up title (remove site name if present)
                    if ' - RÚV' in title:
                        title = title.replace(' - RÚV', '')
            
            # Method 3: Look for specific RÚV title elements
            if not title:
                title_elem = soup.find(['h2', 'h3'], class_=re.compile(r'title|heading'))
                if title_elem:
                    title = title_elem.get_text(strip=True)
            
            if not title:
                title = "Unknown Title"
            
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
                        r'https?://[^\s"<>]+\.m3u8[^\s"<>]*',
                        r'https?://ruv-vod\.akamaized\.net/[^\s"<>]+'
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
    
    def download_with_yt_dlp(self, video_info, episode_title, output_dir="downloads"):
        """Download video using yt-dlp"""
        if not video_info.get('url'):
            print(f"No URL found for: {video_info['title']}")
            return False
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Clean filename using the episode title
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', episode_title)
        output_file = os.path.join(output_dir, f"{safe_title}.mkv")
        
        try:
            cmd = [
                'yt-dlp',
                '--output', output_file,
                '--format', 'best',
                '--merge-output-format', 'mkv',
                '--write-description',
                '--write-info-json',
                '--no-check-certificates',
                '--geo-bypass',
                video_info['url']
            ]
            
            print(f"Downloading: {episode_title}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✓ Successfully downloaded: {episode_title}")
                
                # Find the actual downloaded file
                actual_files = []
                for file in os.listdir(output_dir):
                    if file.startswith(safe_title) and file.endswith('.mkv'):
                        actual_files.append(os.path.join(output_dir, file))
                
                if actual_files:
                    # Get the largest file (main video file)
                    largest_file = max(actual_files, key=os.path.getsize)
                    file_size = os.path.getsize(largest_file)
                    file_size_mb = file_size / (1024 * 1024)
                    print(f"📁 File saved to: {largest_file}")
                    print(f"📊 File size: {file_size_mb:.1f} MB")
                
                return True
            else:
                print(f"✗ yt-dlp failed for {episode_title}")
                print(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error downloading {episode_title}: {e}")
            return False
    
    def scrape_series(self, series_url, download_videos=True):
        """Main method to scrape an entire series"""
        print(f"Starting to scrape series from: {series_url}")
        print("="*60)
        
        # Get all episode links
        episodes = self.get_all_episodes(series_url)
        print(f"Found {len(episodes)} episodes")
        
        if not episodes:
            print("No episodes found. Trying to scrape the single page...")
            video_info = self.extract_video_data(series_url)
            if video_info:
                episodes = [{'url': series_url, 'title': video_info['title']}]
        
        # Determine series folder name
        series_title = episodes[0]['title'] if episodes else 'downloaded_series'
        safe_series_title = re.sub(r'[<>:"/\\|?*]', '_', series_title)
        output_dir = os.path.join('downloads', safe_series_title)
        os.makedirs(output_dir, exist_ok=True)
        
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
                    success = self.download_with_yt_dlp(video_info, episode['title'], output_dir)
                    if not success:
                        print("Download failed, but continuing with other episodes...")
                
                # Be respectful to the server
                time.sleep(3)
            else:
                print(f"Failed to extract video info for: {episode['title']}")
        
        # Save episode information
        info_file = os.path.join(output_dir, 'download_info.json')
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(self.episodes, f, indent=2, ensure_ascii=False)
        print(f"Info file saved to: {info_file}")
        
        print(f"\n" + "="*60)
        print(f"Scraping completed! Found {len(self.episodes)} episodes.")
        print("Episode information saved to download_info.json")
        
        return self.episodes

def main():
    scraper = RUVImprovedScraper()
    
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