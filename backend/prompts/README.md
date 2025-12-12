# Backend Prompts Directory - NeurIPS Academic Grade

This directory contains all AI prompt templates for the Desire-VQA video annotation system, structured for academic research publication standards (NeurIPS/CVPR/ICCV).

## 🎯 Unified Prompt Architecture

All prompts follow **Academic English style** with rigorous theoretical grounding in behavioral psychology and Theory of Mind research.

---

## 📚 **Active Prompt Files** (NeurIPS-Grade)

### **1. annotation_prompts.yaml** ⭐⭐⭐⭐⭐ PRIMARY

**Purpose**: Complete Theory of Mind video annotation with full psychological framework integration

**Components**:
- `knowledge_base`: Shared psychological knowledge base (BDI, Maslow, ToM, Circumplex Model, Desire Dynamics)
- `annotation_v5`: Full academic annotation (6000+ token output)
  - Complete behavioral sequence analysis
  - Desire/motivation transitions
  - Inter-character dynamics
  - Multi-level psychological inference
- `annotation_v3`: Legacy Chinese version (backward compatibility)

**Used by**:
- `scripts/batch_annotate.py` - Primary annotation pipeline

**Output Quality**: Publication-grade research data

---

### **2. content_filter_prompts.yaml** ⭐⭐⭐⭐

**Purpose**: Pre-screening videos for Theory of Mind research data quality

**Components**:
- `content_filter.strict`: Rigorous behavioral observation criteria
- `content_filter.standard`: Moderate quality threshold

**Used by**:
- `backend/content_filter.py` - Video quality assurance

**Key Features**:
- Observable behavior primacy (non-verbal focus)
- Research methodology compliance
- Categorical exclusion rules

---

### **3. question_prompts.yaml** ⭐⭐⭐⭐

**Purpose**: Theory of Mind question-answer dataset construction

**Components**:
- `desire_inference`: Desire/motivation inference questions
- `desire_reasoning`: Reasoning process assessment questions
- `behavioral_sequence_analysis`: Temporal sequence analysis questions

**Used by**:
- `backend/question_generator.py` - VQA dataset generation

**Key Features**:
- Cognitive bias-based distractor design
- Theoretical framework grounding
- Evidence-based reasoning assessment

---

## 🗂️ **Deprecated Files** (Backward Compatibility Only)

### ⚠️ video_analysis_prompts.yaml - DEPRECATED

**Status**: Legacy (Chinese, non-academic style)

**Migration**: Use `annotation_prompts.yaml` → `annotation_v5` instead

**Still used by** (needs migration):
- `backend/vlm_analyzer.py`
- `backend/ai_providers/gemini_provider.py`
- `backend/ai_providers/openai_provider.py`

---

### ⚠️ video_processor_prompts.yaml - DEPRECATED

**Status**: Legacy (Chinese, non-academic style)

**Migration**: Use `annotation_prompts.yaml` → `annotation_v5` instead

**Still used by** (needs migration):
- `backend/video_processor_v2.py`

---

## 🚀 **Quick Start Guide**

### For Video Annotation (Primary Pipeline)

```python
from backend.prompt_loader import PromptLoader

# Load annotation prompts
loader = PromptLoader("backend/prompts/annotation_prompts.yaml")

# Get full academic annotation prompt
prompt = loader.get_prompt("annotation_v5.template")

# Get knowledge base for reference
knowledge_base = loader.prompts.get("knowledge_base", {})
```

**CLI Usage**:
```bash
# Batch annotation with V5 academic prompts
python scripts/batch_annotate.py \
  --video-dir data/Youtube_videos \
  --output-dir data/annotations \
  --model gemini-2.0-flash-exp
```

---

### For Content Filtering

```python
from backend.content_filter import ContentFilter

# Initialize filter
filter = ContentFilter()

# Check video (strict mode)
result = await filter.check_video_content(
    video_path="path/to/video.mp4",
    strict_mode=True
)

print(f"Pass: {result['pass']}, Reason: {result['reason']}")
```

---

### For Question Generation

```python
from backend.question_generator import QuestionGenerator
from backend.prompt_loader import PromptLoader

# Initialize
loader = PromptLoader("backend/prompts/question_prompts.yaml")
generator = QuestionGenerator(ai_provider, loader)

# Generate questions from annotation
questions = generator.generate_questions_for_video(
    video_id="video_001",
    annotation_data=annotation,
    num_questions=10
)
```

---

## 📖 **Theoretical Frameworks Integrated**

All prompts incorporate rigorous psychological theory:

| Framework | Reference | Application |
|-----------|-----------|-------------|
| **BDI Model** | Bratman (1987) | Belief-Desire-Intention mental state attribution |
| **Maslow's Hierarchy** | Maslow (1943) | Need-level classification (physiological → self-actualization) |
| **Theory of Mind** | Wellman (2014); Apperly & Butterfill (2009) | Mental state inference from observable behavior |
| **Circumplex Model** | Russell (1980) | Emotion characterization (valence × arousal) |
| **Desire Dynamics** | Original framework | Temporal transition analysis (7 types) |

---

## 🔧 **Prompt Design Principles**

1. **Academic Rigor**: All prompts use formal academic English
2. **Behavioral Primacy**: Focus on observable non-verbal cues
3. **Theoretical Grounding**: Explicit references to psychological frameworks
4. **Parsimony Principle**: Prefer lower-level explanations (Occam's Razor)
5. **Evidence-Based**: Every inference must cite specific behavioral observations
6. **Reproducibility**: Clear schemas for inter-annotator consistency

---

## 📊 **Output Quality Standards**

| Aspect | Standard |
|--------|----------|
| **Language** | Academic English (NeurIPS/CVPR grade) |
| **Terminology** | Snake_Case psychological labels (e.g., `Social_Affiliation_Seeking`) |
| **Evidence** | Timestamped behavioral observations |
| **Confidence** | Explicit uncertainty quantification |
| **Alternatives** | Multiple interpretation consideration |
| **Schema** | Strict JSON with validation |

---

## 🔬 **For Academic Publication**

When citing this annotation system in research:

```bibtex
@inproceedings{desire-vqa-2025,
  title={Desire-VQA: Theory of Mind Video Question Answering via Desire/Motivation Analysis},
  author={[Your Name]},
  booktitle={Advances in Neural Information Processing Systems (NeurIPS)},
  year={2025},
  note={Annotation prompts available at: backend/prompts/annotation_prompts.yaml}
}
```

**Key Features for Paper**:
- **Knowledge Base**: 5 integrated psychological frameworks
- **Open-ended Inference**: No predefined label vocabulary
- **Temporal Precision**: Onset/offset timestamps for transitions
- **Multi-level Analysis**: From physiological to self-actualization needs
- **Reproducible Schema**: Complete JSON specification for replication

---

## 🛠️ **Adding New Prompts**

1. **Create YAML entry** in appropriate file:
   ```yaml
   my_new_task:
     description: "Academic description of task"
     version: "1.0-academic"
     template: |
       # Academic English prompt here

       ## Theoretical Framework
       [Reference psychological theories]

       ## Task Specification
       [Clear instructions]

       ## Output Format
       ```json
       {...}
       ```
   ```

2. **Load in Python**:
   ```python
   loader = PromptLoader("backend/prompts/your_file.yaml")
   prompt = loader.get_prompt("my_new_task.template", var1="value1")
   ```

3. **Test thoroughly** with edge cases and validate academic quality

---

## 📞 **Support & Migration**

For questions about:
- **Prompt usage**: Check Quick Start Guide above
- **Migrating from deprecated files**: See deprecation warnings in legacy files
- **Academic quality review**: Ensure alignment with NeurIPS publication standards
- **Custom prompt development**: Follow existing academic style and theoretical grounding

---

## ✅ **Checklist for NeurIPS Submission**

- [x] All prompts in Academic English
- [x] Explicit theoretical framework references
- [x] Behavioral observation primacy
- [x] Reproducible JSON schemas
- [x] Inter-annotator consistency guidelines
- [x] Open-ended inference (no fixed vocabularies)
- [x] Temporal precision requirements
- [x] Confidence and alternative interpretations
- [x] Edge case handling protocols

---

**Last Updated**: 2025-12-07
**Version**: 2.0-academic
**Maintained by**: Desire-VQA Research Team
