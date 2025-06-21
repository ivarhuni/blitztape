import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time
from urllib.parse import urljoin, urlparse
import subprocess
import sys

class RUVScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_url = "https://www.ruv.is"
        self.episodes = []
        
    def get_episode_links(self, series_url):
        """Extract all episode links from a series page"""
        try:
            response = self.session.get(series_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for episode links - this might need adjustment based on actual HTML structure
            episode_links = []
            
            # Try different selectors to find episode links
            selectors = [
                'a[href*="/spila/"]',
                '.episode-link',
                '.video-link',
                'a[href*="b85s4f"]',
                'a[href*="37768"]'
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href and '/spila/' in href:
                        full_url = urljoin(self.base_url, href)
                        if full_url not in [ep['url'] for ep in episode_links]:
                            episode_links.append({
                                'url': full_url,
                                'title': link.get_text(strip=True) or 'Unknown Episode'
                            })
            
            return episode_links
            
        except Exception as e:
            print(f"Error getting episode links: {e}")
            return []
    
    def extract_video_info(self, episode_url):
        """Extract video information from an episode page"""
        try:
            response = self.session.get(episode_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.find('h1')
            title = title.get_text(strip=True) if title else 'Unknown Title'
            
            # Look for video player or video source
            video_info = {
                'title': title,
                'url': episode_url,
                'video_url': None,
                'description': ''
            }
            
            # Try to find video source in various ways
            # Method 1: Look for video tags
            video_tags = soup.find_all('video')
            for video in video_tags:
                src = video.get('src')
                if src:
                    video_info['video_url'] = urljoin(self.base_url, src)
                    break
            
            # Method 2: Look for source tags
            if not video_info['video_url']:
                source_tags = soup.find_all('source')
                for source in source_tags:
                    src = source.get('src')
                    if src:
                        video_info['video_url'] = urljoin(self.base_url, src)
                        break
            
            # Method 3: Look for iframe with video player
            if not video_info['video_url']:
                iframes = soup.find_all('iframe')
                for iframe in iframes:
                    src = iframe.get('src')
                    if src and ('player' in src or 'video' in src):
                        video_info['video_url'] = src
                        break
            
            # Method 4: Look for JavaScript variables containing video URLs
            if not video_info['video_url']:
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string:
                        # Look for common video URL patterns
                        patterns = [
                            r'"videoUrl"\s*:\s*"([^"]+)"',
                            r'"src"\s*:\s*"([^"]+\.mp4[^"]*)"',
                            r'"url"\s*:\s*"([^"]+\.mp4[^"]*)"',
                            r'https?://[^\s"<>]+\.mp4[^\s"<>]*'
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, script.string)
                            if matches:
                                video_info['video_url'] = matches[0]
                                break
                    
                    if video_info['video_url']:
                        break
            
            # Extract description
            desc_elem = soup.find('meta', {'name': 'description'})
            if desc_elem:
                video_info['description'] = desc_elem.get('content', '')
            
            return video_info
            
        except Exception as e:
            print(f"Error extracting video info from {episode_url}: {e}")
            return None
    
    def download_video(self, video_info, output_dir="downloads"):
        """Download a video using yt-dlp or similar tool"""
        if not video_info.get('video_url'):
            print(f"No video URL found for: {video_info['title']}")
            return False
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Clean filename
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', video_info['title'])
        output_file = os.path.join(output_dir, f"{safe_title}.mp4")
        
        try:
            # Try using yt-dlp first (recommended)
            cmd = [
                'yt-dlp',
                '--output', output_file,
                '--format', 'best',
                video_info['url']  # Use the episode page URL, not direct video URL
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"Successfully downloaded: {video_info['title']}")
                return True
            else:
                print(f"yt-dlp failed for {video_info['title']}: {result.stderr}")
                
                # Fallback: try direct download with requests
                print("Trying direct download...")
                response = self.session.get(video_info['video_url'], stream=True)
                response.raise_for_status()
                
                with open(output_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                print(f"Direct download completed: {video_info['title']}")
                return True
                
        except Exception as e:
            print(f"Error downloading {video_info['title']}: {e}")
            return False
    
    def scrape_series(self, series_url, download_videos=True):
        """Main method to scrape an entire series"""
        print(f"Starting to scrape series from: {series_url}")
        
        # Get all episode links
        episode_links = self.get_episode_links(series_url)
        print(f"Found {len(episode_links)} episodes")
        
        if not episode_links:
            print("No episodes found. Trying to scrape the single page...")
            # If no episode links found, try to scrape the single page
            video_info = self.extract_video_info(series_url)
            if video_info:
                episode_links = [{'url': series_url, 'title': video_info['title']}]
        
        # Extract video information for each episode
        for i, episode in enumerate(episode_links, 1):
            print(f"\nProcessing episode {i}/{len(episode_links)}: {episode['title']}")
            
            video_info = self.extract_video_info(episode['url'])
            if video_info:
                self.episodes.append(video_info)
                print(f"Title: {video_info['title']}")
                print(f"Video URL: {video_info['video_url']}")
                
                if download_videos:
                    self.download_video(video_info)
                
                # Add delay to be respectful to the server
                time.sleep(2)
            else:
                print(f"Failed to extract video info for: {episode['title']}")
        
        # Save episode information to JSON
        with open('episodes.json', 'w', encoding='utf-8') as f:
            json.dump(self.episodes, f, indent=2, ensure_ascii=False)
        
        print(f"\nScraping completed! Found {len(self.episodes)} episodes.")
        print("Episode information saved to episodes.json")
        
        return self.episodes

def main():
    # Example usage
    scraper = RUVScraper()
    
    # The series URL you provided
    series_url = "https://www.ruv.is/sjonvarp/spila/sammi-brunavordur-x/37768/b85s4f"
    
    # Scrape the series (set download_videos=False if you only want to extract info)
    episodes = scraper.scrape_series(series_url, download_videos=True)
    
    # Print summary
    print("\n" + "="*50)
    print("EPISODE SUMMARY")
    print("="*50)
    for i, episode in enumerate(episodes, 1):
        print(f"{i}. {episode['title']}")
        if episode.get('video_url'):
            print(f"   Video URL: {episode['video_url']}")
        print()

if __name__ == "__main__":
    main() 