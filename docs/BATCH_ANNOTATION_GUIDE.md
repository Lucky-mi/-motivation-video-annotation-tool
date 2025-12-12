# Batch Video Annotation Guide - NeurIPS Academic Grade

Complete guide for running batch video annotation with **annotation_v5** prompts (Academic English, Theory of Mind framework).

---

## 🎯 Quick Start

### **Basic Usage**

```bash
python scripts/batch_annotate.py \
  --video-dir data/Youtube_videos \
  --output-dir data/annotations \
  --model gemini-2.0-flash-exp
```

This will:
1. Scan `data/Youtube_videos` for video files
2. Annotate each video using **annotation_v5** (NeurIPS-grade academic prompts)
3. Save JSON annotations to `data/annotations`
4. Skip already-annotated videos automatically

---

## 📋 Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--video-dir` | `data/Youtube_videos` | Directory containing videos to annotate |
| `--output-dir` | `data/annotations_test` | Where to save annotation JSON files |
| `--limit` | None | Max number of videos to process (e.g., `--limit 10`) |
| `--model` | `gemini-2.0-flash-exp` | Gemini model to use |
| `--dry-run` | False | Show what would be processed without actually processing |

---

## 🚀 Usage Examples

### **1. Preview What Will Be Processed**

```bash
python scripts/batch_annotate.py \
  --video-dir data/Youtube_videos \
  --dry-run
```

Output example:
```
🔍 DRY RUN - Would process 127 videos:
   1. conflict_scene_001.mp4
   2. emotional_reaction_012.mp4
   3. social_interaction_045.mp4
   ...
```

---

### **2. Test on Small Batch**

```bash
python scripts/batch_annotate.py \
  --video-dir data/Youtube_videos \
  --output-dir data/annotations_test \
  --limit 5
```

Annotates only the first 5 videos (useful for testing).

---

### **3. Full Production Run**

```bash
python scripts/batch_annotate.py \
  --video-dir data/Youtube_videos \
  --output-dir data/annotations \
  --model gemini-2.0-flash-exp
```

**Pro tip**: The script automatically skips already-annotated videos, so you can safely interrupt and resume!

---

### **4. Use Different Model**

```bash
python scripts/batch_annotate.py \
  --video-dir data/Youtube_videos \
  --model gemini-2.5-flash  # or gemini-1.5-pro
```

---

## 📊 Output Format

### **File Structure**

```
data/annotations/
├── video_001.json          # Complete annotation
├── video_002.json
├── video_003_raw.txt       # Raw response if JSON parsing failed
└── ...
```

### **JSON Schema** (annotation_v5)

Each annotation JSON contains:

```json
{
  "video_id": "video_001",
  "video_path": "data/Youtube_videos/video_001.mp4",
  "duration_seconds": 45.2,
  "annotation_timestamp": "2025-12-07T10:30:15",
  "annotation_model": "gemini-2.0-flash-exp",

  "scene_context": {
    "physical_setting": "...",
    "social_context": "...",
    "emotional_atmosphere": "..."
  },

  "characters": [
    {
      "character_id": "person_blue_shirt",
      "physical_description": "...",
      "role_in_scene": "...",
      "initial_state": {...},
      "final_state": {...},
      "attribute_dynamics": [...]
    }
  ],

  "desire_motivation_analysis": [
    {
      "character_id": "person_blue_shirt",
      "desire_label": "Social_Affiliation_Seeking",
      "maslow_level": "belonging",
      "desire_type": "intrinsic",
      "intensity": "moderate",
      "temporal_scope": {
        "start_seconds": 5.2,
        "end_seconds": 15.8
      },
      "reasoning_chain": "...",
      "supporting_evidence": [...],
      "confidence": "high"
    }
  ],

  "desire_transitions": [
    {
      "character_id": "person_blue_shirt",
      "transition_type": "transformation",
      "onset_timestamp_seconds": 15.2,
      "offset_timestamp_seconds": 16.5,
      "trigger_event": "...",
      "desire_before": {...},
      "desire_after": {...},
      "visual_marker_of_change": "..."
    }
  ],

  "key_segments_for_qa": [...],

  "annotation_metadata": {
    "annotation_version": "5.0",
    "frameworks_applied": ["BDI", "Maslow", "ToM", "Circumplex"],
    "overall_annotation_confidence": "high"
  }
}
```

---

## ⚙️ Configuration

### **Environment Variables**

Create a `.env` file in project root:

```bash
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
```

Or set directly:
```bash
export GEMINI_API_KEY="your_api_key_here"
```

---

### **Prompt Customization**

The script uses `backend/prompts/annotation_prompts.yaml` → `annotation_v5`.

To customize:
1. Edit `backend/prompts/annotation_prompts.yaml`
2. Modify the `annotation_v5.template` section
3. Re-run annotation (already-annotated videos will be skipped unless you delete their JSON files)

---

## 🔄 **Resume Interrupted Processing**

The script has **automatic resume** functionality:

1. **First run** (interrupted after 50 videos):
   ```bash
   python scripts/batch_annotate.py --video-dir data/Youtube_videos
   # Ctrl+C after some time
   ```

2. **Resume** (automatically skips completed videos):
   ```bash
   python scripts/batch_annotate.py --video-dir data/Youtube_videos
   # Will skip the 50 already-annotated videos
   ```

**No special flags needed** - it automatically checks for existing annotations!

---

## 📈 **Monitoring Progress**

### **Real-Time Output**

```
[1/127] Processing: conflict_scene_001.mp4
📤 Uploading video to Gemini...
✅ Uploaded: files/xyz123
⏳ Waiting for video processing...
✅ Video processing complete
🤖 Generating annotation...
✅ Annotation saved: data/annotations/conflict_scene_001.json

[2/127] Processing: emotional_reaction_012.mp4
...

📊 Progress: 50 success, 2 failed, 25 skipped
```

### **Final Report**

```
============================================================
📊 FINAL REPORT
============================================================
   Total videos: 127
   ✅ Success: 115
   ❌ Failed: 5
   ⏭️  Skipped: 7
============================================================
```

---

## 🐛 **Troubleshooting**

### **Issue 1: JSON Parsing Errors**

If you see:
```
⚠️ JSON parse error (attempt 1/3): Expecting value: line 1 column 1
```

**Solution**: The script automatically retries 3 times. If it still fails, a raw response file (`video_xxx_raw.txt`) is saved for debugging.

---

### **Issue 2: API Rate Limits**

```
Error: 429 Too Many Requests
```

**Solution**: Add delay between requests (modify `scripts/batch_annotate.py`):

```python
# In process_batch method, after each video:
import time
time.sleep(5)  # 5 second delay
```

---

### **Issue 3: Video Processing Timeout**

```
❌ Processing failed: Video processing failed: PROCESSING_FAILED
```

**Solution**:
- Check video file integrity
- Ensure video format is supported (mp4, avi, mov, mkv)
- Try with a smaller/shorter video

---

### **Issue 4: Out of Memory**

**Solution**: Process in smaller batches using `--limit`:

```bash
# Process 20 videos at a time
python scripts/batch_annotate.py --video-dir data/Youtube_videos --limit 20
```

---

## 📊 **Performance Expectations**

| Video Length | Processing Time | Cost (Gemini 2.0 Flash) |
|--------------|----------------|-------------------------|
| 30 seconds | ~20-30s | ~$0.0001 |
| 1 minute | ~40-60s | ~$0.0002 |
| 3 minutes | ~90-120s | ~$0.0005 |
| 5 minutes | ~150-200s | ~$0.001 |

**For 100 videos (avg 2min each)**:
- Time: ~2-3 hours
- Cost: ~$0.02-0.05

---

## 🎓 **Academic Quality Assurance**

The annotations follow **NeurIPS publication standards**:

✅ **Theoretical Grounding**:
- BDI Model (Bratman, 1987)
- Maslow's Hierarchy (1943)
- Theory of Mind (Wellman, 2014)
- Circumplex Model (Russell, 1980)

✅ **Methodological Rigor**:
- Parsimony Principle applied
- Behavioral observation primacy
- Confidence quantification
- Alternative interpretations considered

✅ **Reproducibility**:
- Complete JSON schema
- Timestamped evidence
- Inter-annotator consistency guidelines
- Open-ended inference (no fixed vocabularies)

---

## 📚 **Next Steps After Annotation**

Once you have annotations, you can:

### **1. Generate VQA Questions**

```python
from backend.question_generator import QuestionGenerator

# Load annotation
with open("data/annotations/video_001.json") as f:
    annotation = json.load(f)

# Generate questions
generator = QuestionGenerator(ai_provider)
questions = generator.generate_questions_for_video(
    video_id="video_001",
    annotation_data=annotation,
    num_questions=10
)
```

### **2. Extract Video Clips**

```python
from backend.vqa_processor import VQAProcessor

processor = VQAProcessor()
vqa_data = processor.process_annotation_to_vqa(
    video_path="data/Youtube_videos/video_001.mp4",
    annotation_path="data/annotations/video_001.json",
    extract_clips=True
)
```

### **3. Statistical Analysis**

```python
import json
from pathlib import Path

# Load all annotations
annotations = []
for json_file in Path("data/annotations").glob("*.json"):
    with open(json_file) as f:
        annotations.append(json.load(f))

# Analyze desire distribution
desire_counts = {}
for ann in annotations:
    for desire in ann["desire_motivation_analysis"]:
        label = desire["desire_label"]
        desire_counts[label] = desire_counts.get(label, 0) + 1

# Print top 10 desires
for label, count in sorted(desire_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"{label}: {count}")
```

---

## 🔬 **Citation**

If using this annotation system in academic work:

```bibtex
@inproceedings{desire-vqa-2025,
  title={Desire-VQA: Theory of Mind Video Question Answering via Desire/Motivation Analysis},
  author={[Your Name]},
  booktitle={Advances in Neural Information Processing Systems (NeurIPS)},
  year={2025}
}
```

---

**Last Updated**: 2025-12-07
**Script Location**: `scripts/batch_annotate.py`
**Prompt Version**: annotation_v5 (Academic English, NeurIPS-grade)
