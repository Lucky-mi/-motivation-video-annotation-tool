# scripts/batch_annotate_v2.py
"""
Batch Video Annotation Script V2
Processes videos using Gemini with V5.1 annotation prompts

Improvements over V1:
- Includes knowledge_base in prompt
- Better JSON extraction with fallback
- Adds frame sampling info
- Improved error messages
"""
import asyncio
import json
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import argparse
import time
import yaml
import cv2

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False


class PromptLoaderV2:
    """Simple YAML prompt loader that preserves structure"""
    
    def __init__(self, yaml_path: str):
        self.yaml_path = Path(yaml_path)
        if not self.yaml_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {yaml_path}")
        
        with open(self.yaml_path, 'r', encoding='utf-8') as f:
            self.prompts = yaml.safe_load(f)
    
    def get_knowledge_base_text(self) -> str:
        """Convert knowledge_base dict to formatted text for prompt"""
        kb = self.prompts.get("knowledge_base", {})
        if not kb:
            return ""
        
        # Convert to YAML string for readability
        return yaml.dump(kb, default_flow_style=False, allow_unicode=True, width=120)
    
    def get_annotation_template(self) -> str:
        """Get the annotation template - tries v6 first, falls back to v5"""
        return self.prompts.get("annotation_v6", self.prompts.get("annotation_v5", {})).get("template", "")
    
    def get_output_control(self) -> str:
        """Get output control guidelines"""
        oc = self.prompts.get("output_control", {})
        if not oc:
            return ""
        return yaml.dump(oc, default_flow_style=False, allow_unicode=True)
    
    def get_full_prompt(self) -> str:
        """Assemble the complete prompt with knowledge base + template"""
        parts = []
        
        # 1. Knowledge Base
        kb_text = self.get_knowledge_base_text()
        if kb_text:
            parts.append("# PSYCHOLOGICAL KNOWLEDGE BASE\n")
            parts.append("Use this knowledge base to guide your psychological inference:\n\n")
            parts.append(f"```yaml\n{kb_text}```\n\n")
        
        # 2. Output Control (important for length management)
        oc_text = self.get_output_control()
        if oc_text:
            parts.append("# OUTPUT CONTROL GUIDELINES\n")
            parts.append(f"```yaml\n{oc_text}```\n\n")
        
        # 3. Main Template
        template = self.get_annotation_template()
        if template:
            parts.append(template)
        
        return "\n".join(parts)


class BatchAnnotatorV2:
    """Batch video annotator using Gemini - V2 with improvements"""
    
    def __init__(
        self,
        prompt_path: str = "backend/prompts/annotation_prompts_v6.yaml",
        output_dir: str = "data/annotations_v6",
        model_name: str = "gemini-3.1-pro-preview",
        max_retries: int = 3,
        retry_delay: int = 30
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.model_name = model_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Initialize Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package not installed. Run: pip install google-generativeai")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        
        # Load prompts with V2 loader
        self.prompt_loader = PromptLoaderV2(prompt_path)
        self.full_prompt = self.prompt_loader.get_full_prompt()
        
        print(f"📝 Loaded prompt ({len(self.full_prompt)} chars)")
        
        # Statistics
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "start_time": None,
            "errors": []
        }
    
    def extract_json_from_response(self, text: str) -> dict:
        """
        Extract JSON from model response with multiple fallback strategies
        """
        # Strategy 1: Look for ```json ... ```
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Strategy 2: Look for any ``` ... ```
        code_match = re.search(r'```\s*([\s\S]*?)\s*```', text)
        if code_match:
            try:
                return json.loads(code_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Strategy 3: Find JSON object boundaries { ... }
        # Find the first { and last }
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        if first_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(text[first_brace:last_brace + 1])
            except json.JSONDecodeError:
                pass
        
        # Strategy 4: Try the whole text
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        raise json.JSONDecodeError("Could not extract valid JSON from response", text, 0)
    
    def annotate_video(self, video_path: str) -> Dict:
        """Annotate a single video"""
        video_path = Path(video_path)
        video_id = video_path.stem
        
        print(f"\n{'='*60}")
        print(f"📹 Processing: {video_path.name}")
        print(f"{'='*60}")
        
        # Check if already annotated
        output_file = self.output_dir / f"{video_id}.json"
        if output_file.exists():
            print(f"⏭️  Skipping (already annotated): {output_file.name}")
            self.stats["skipped"] += 1
            return {"status": "skipped", "video_id": video_id}
        
        # Upload video
        print("📤 Uploading video to Gemini...")
        video_file = None
        try:
            video_file = genai.upload_file(path=str(video_path))
            print(f"✅ Uploaded: {video_file.name}")
        except Exception as e:
            error_msg = f"Upload failed: {e}"
            print(f"❌ {error_msg}")
            self.stats["failed"] += 1
            self.stats["errors"].append({"video_id": video_id, "error": error_msg})
            return {"status": "failed", "error": error_msg, "video_id": video_id}
        
        # Wait for processing
        print("⏳ Waiting for video processing...")
        try:
            wait_count = 0
            while video_file.state.name == "PROCESSING":
                time.sleep(5)
                wait_count += 1
                if wait_count % 6 == 0:  # Every 30 seconds
                    print(f"   Still processing... ({wait_count * 5}s)")
                video_file = genai.get_file(video_file.name)
            
            if video_file.state.name != "ACTIVE":
                raise ValueError(f"Video processing failed with state: {video_file.state.name}")
            
            print("✅ Video ready for annotation")
        except Exception as e:
            error_msg = f"Processing failed: {e}"
            print(f"❌ {error_msg}")
            self.stats["failed"] += 1
            self.stats["errors"].append({"video_id": video_id, "error": error_msg})
            self._cleanup_file(video_file)
            return {"status": "failed", "error": error_msg, "video_id": video_id}
        
        # Generate annotation
        print("🤖 Generating annotation (this may take 1-3 minutes)...")
        
        for attempt in range(self.max_retries):
            try:
                # Inject video duration into Time Wall placeholder
                cap = cv2.VideoCapture(str(video_path))
                video_duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / max(cap.get(cv2.CAP_PROP_FPS), 1)
                cap.release()
                prompt_with_duration = self.full_prompt.replace("{duration}", f"{video_duration:.1f}")
                
                response = self.model.generate_content(
                    [video_file, prompt_with_duration],
                    request_options={"timeout": 600},
                    generation_config={
                        "temperature": 0.2,  # Lower temperature for more consistent output
                        "max_output_tokens": 16384,  # Increased for DDF v6.1 verbose output
                    }
                )
                
                result_text = response.text
                
                # Extract and parse JSON
                annotation = self.extract_json_from_response(result_text)
                
                # Add/update metadata
                annotation["video_id"] = video_id
                annotation["video_path"] = str(video_path)
                annotation["annotation_timestamp"] = datetime.now().isoformat()
                annotation["annotation_metadata"] = annotation.get("annotation_metadata", {})
                annotation["annotation_metadata"]["model_used"] = self.model_name
                annotation["annotation_metadata"]["prompt_version"] = "6.1"
                
                # Validate basic structure
                required_keys = ["characters", "desire_motivation_analysis"]
                missing_keys = [k for k in required_keys if k not in annotation]
                if missing_keys:
                    raise ValueError(f"Missing required keys in annotation: {missing_keys}")
                
                # Post-processing: clamp all timestamps to [0, duration]
                duration = annotation.get("duration_seconds", video_duration)
                clamped = [0]  # mutable counter
                def clamp_timestamps(obj):
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            if isinstance(v, (int, float)) and ("timestamp" in k or k in ("start_seconds", "end_seconds")):
                                if v > duration:
                                    obj[k] = duration
                                    clamped[0] += 1
                                elif v < 0:
                                    obj[k] = 0.0
                                    clamped[0] += 1
                            else:
                                clamp_timestamps(v)
                    elif isinstance(obj, list):
                        for item in obj:
                            clamp_timestamps(item)
                clamp_timestamps(annotation)
                if clamped[0]:
                    print(f"   🔧 Clamped {clamped[0]} out-of-range timestamp(s) to [0, {duration}]")
                
                # Save annotation
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(annotation, f, ensure_ascii=False, indent=2)
                
                print(f"✅ Annotation saved: {output_file.name}")
                print(f"   - Characters: {len(annotation.get('characters', []))}")
                print(f"   - Desire analyses: {len(annotation.get('desire_motivation_analysis', []))}")
                print(f"   - Transitions: {len(annotation.get('desire_transitions', []))}")
                
                self.stats["success"] += 1
                self._cleanup_file(video_file)
                
                return {"status": "success", "video_id": video_id, "output": str(output_file)}
                
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parse error (attempt {attempt + 1}/{self.max_retries}): {e}")
                # Always save raw response for debugging
                raw_file = self.output_dir / f"{video_id}_raw_attempt{attempt+1}.txt"
                with open(raw_file, 'w', encoding='utf-8') as f:
                    f.write(f"Error: {e}\n\n")
                    f.write("="*60 + "\n")
                    f.write(result_text)
                print(f"   📄 Raw response saved: {raw_file.name}")
                print(f"   📝 First 200 chars: {result_text[:200]}")
                sys.stdout.flush()
                if attempt < self.max_retries - 1:
                    print(f"   Retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"   ❌ All retries exhausted.")
                    self.stats["failed"] += 1
                    self.stats["errors"].append({"video_id": video_id, "error": f"JSON parse: {e}"})
                    
            except Exception as e:
                print(f"⚠️  Error (attempt {attempt + 1}/{self.max_retries}): {e}")
                sys.stdout.flush()
                if attempt < self.max_retries - 1:
                    print(f"   Retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                else:
                    self.stats["failed"] += 1
                    self.stats["errors"].append({"video_id": video_id, "error": str(e)})
        
        self._cleanup_file(video_file)
        return {"status": "failed", "error": "Max retries exceeded", "video_id": video_id}
    
    def _cleanup_file(self, video_file):
        """Clean up uploaded file"""
        if video_file:
            try:
                genai.delete_file(video_file.name)
            except:
                pass
    
    def process_batch(
        self,
        video_dir: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Process a batch of videos"""
        video_dir = Path(video_dir)
        
        if not video_dir.exists():
            raise ValueError(f"Video directory not found: {video_dir}")
        
        # Find video files (sorted by name)
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'}
        video_files = sorted([
            f for f in video_dir.glob('*')
            if f.suffix.lower() in video_extensions and not f.name.endswith('.part')
        ])
        
        # Apply manual review filter if available
        review_filter_path = Path("data/manual_review_status.json")
        if review_filter_path.exists():
            with open(review_filter_path, 'r', encoding='utf-8') as rf:
                review_status = json.load(rf)
            keep_set = {k for k, v in review_status.items() if v == 'keep'}
            before_count = len(video_files)
            video_files = [f for f in video_files if f.name in keep_set]
            print(f"🔍 Review filter: {before_count} → {len(video_files)} (only 'keep' videos)")
            sys.stdout.flush()
        
        print(f"\n{'#'*60}")
        print(f"# Batch Video Annotation - DDF v6.1")
        print(f"{'#'*60}")
        print(f"📂 Source: {video_dir}")
        print(f"📁 Output: {self.output_dir}")
        print(f"🎬 Videos to annotate: {len(video_files)}")
        print(f"🤖 Model: {self.model_name}")
        sys.stdout.flush()
        
        if limit:
            video_files = video_files[:limit]
            print(f"📊 Processing limit: {limit}")
        
        # Count already done
        existing = sum(1 for v in video_files if (self.output_dir / f"{v.stem}.json").exists())
        print(f"✅ Already annotated: {existing}")
        print(f"📝 To process: {len(video_files) - existing}")
        print(f"{'#'*60}\n")
        sys.stdout.flush()
        
        self.stats["total"] = len(video_files)
        self.stats["start_time"] = time.time()
        results = []
        
        for i, video_path in enumerate(video_files):
            print(f"\n[{i+1}/{len(video_files)}]", end="", flush=True)
            result = self.annotate_video(str(video_path))
            results.append(result)
            
            # Progress report every 10 videos
            if (i + 1) % 10 == 0:
                self._print_progress()
        
        # Final report
        self._print_final_report()
        
        # Save error log if there were failures
        if self.stats["errors"]:
            error_log = self.output_dir / "annotation_errors.json"
            with open(error_log, 'w', encoding='utf-8') as f:
                json.dump(self.stats["errors"], f, ensure_ascii=False, indent=2)
            print(f"\n📋 Error log saved: {error_log}")
        
        return results
    
    def _print_progress(self):
        """Print current progress"""
        elapsed = time.time() - self.stats["start_time"]
        processed = self.stats["success"] + self.stats["failed"]
        if processed > 0:
            avg_time = elapsed / processed
            remaining = self.stats["total"] - processed - self.stats["skipped"]
            eta = avg_time * remaining
            print(f"\n📊 Progress: {self.stats['success']} ✅ | {self.stats['failed']} ❌ | {self.stats['skipped']} ⏭️")
            print(f"   ETA: {eta/60:.1f} minutes ({remaining} videos left)")
    
    def _print_final_report(self):
        """Print final statistics"""
        elapsed = time.time() - self.stats["start_time"]
        
        print(f"\n{'='*60}")
        print("📊 FINAL REPORT")
        print(f"{'='*60}")
        print(f"   Total videos: {self.stats['total']}")
        print(f"   ✅ Success: {self.stats['success']}")
        print(f"   ❌ Failed: {self.stats['failed']}")
        print(f"   ⏭️  Skipped: {self.stats['skipped']}")
        print(f"   ⏱️  Time: {elapsed/60:.1f} minutes")
        if self.stats['success'] > 0:
            print(f"   📈 Avg time per video: {elapsed/self.stats['success']:.1f}s")
        print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Batch Video Annotation V2 - ToM/Desire Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would be processed
  python batch_annotate_v2.py --limit 77 --dry-run
  
  # Test with 1 video first
  python batch_annotate_v2.py --limit 1
  
  # Process first 77 videos
  python batch_annotate_v2.py --limit 77
  
  # Resume interrupted batch (skips existing)
  python batch_annotate_v2.py --limit 77
        """
    )
    parser.add_argument(
        "--video-dir",
        type=str,
        default="data/Youtube_videos",
        help="Directory containing videos (default: data/Youtube_videos)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/annotations_v6",
        help="Output directory for annotations (default: data/annotations_test)"
    )
    parser.add_argument(
        "--prompt-file",
        type=str,
        default="backend/prompts/annotation_prompts_v6.yaml",
        help="Path to prompt YAML file"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of videos to process"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-3.1-pro-preview",
        help="Gemini model to use (default: gemini-3.1-pro-preview)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without actually processing"
    )
    
    args = parser.parse_args()
    
    # Dry run mode
    if args.dry_run:
        video_dir = Path(args.video_dir)
        output_dir = Path(args.output_dir)
        
        if not video_dir.exists():
            print(f"❌ Video directory not found: {video_dir}")
            return
        
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'}
        video_files = sorted([
            f for f in video_dir.glob('*')
            if f.suffix.lower() in video_extensions and not f.name.endswith('.part')
        ])
        
        if args.limit:
            video_files = video_files[:args.limit]
        
        # Check existing
        existing = []
        to_process = []
        for f in video_files:
            if (output_dir / f"{f.stem}.json").exists():
                existing.append(f)
            else:
                to_process.append(f)
        
        print(f"\n🔍 DRY RUN - Analysis for {len(video_files)} videos:\n")
        print(f"   ✅ Already annotated: {len(existing)}")
        print(f"   📝 To be processed: {len(to_process)}")
        
        if to_process:
            print(f"\n📋 Videos to process (first 20):")
            for i, f in enumerate(to_process[:20]):
                print(f"   {i+1}. {f.name}")
            if len(to_process) > 20:
                print(f"   ... and {len(to_process) - 20} more")
        
        return
    
    # Check prompt file exists
    if not Path(args.prompt_file).exists():
        print(f"❌ Prompt file not found: {args.prompt_file}")
        print(f"   Please copy annotation_prompts_v5.1_final.yaml to this location")
        return
    
    # Run batch annotation
    try:
        annotator = BatchAnnotatorV2(
            prompt_path=args.prompt_file,
            output_dir=args.output_dir,
            model_name=args.model
        )
        
        annotator.process_batch(
            video_dir=args.video_dir,
            limit=args.limit
        )
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()