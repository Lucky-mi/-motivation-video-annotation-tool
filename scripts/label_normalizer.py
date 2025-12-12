#!/usr/bin/env python3
"""
Desire Label Normalization & Clustering
========================================
Post-processes annotation files to standardize and cluster desire labels.

Usage:
    python label_normalizer.py --input-dir data/annotations_test --output-dir data/annotations_normalized
    python label_normalizer.py --input-dir data/annotations_test --dry-run  # Preview changes
"""

import json
import argparse
import re
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional
from copy import deepcopy


class LabelNormalizer:
    """Normalizes and clusters desire/emotion labels for consistency."""
    
    # =========================================================================
    # DESIRE LABEL MAPPING
    # =========================================================================
    # Maps specific labels to canonical forms
    # Format: "original_label": "canonical_label"
    
    DESIRE_LABEL_MAP = {
        # ----- Social/Affiliation Cluster -----
        "Social_Affiliation_Seeking": "Social_Affiliation_Seeking",
        "Social_Affiliation_Maintenance": "Social_Affiliation_Seeking",
        "Social_Connection_Initiation": "Social_Affiliation_Seeking",
        "Social_Inclusion_Maintenance": "Social_Affiliation_Seeking",
        "Social_Relationship_Maintenance": "Social_Affiliation_Seeking",
        "Social_PairBonding_Initiation": "Social_Affiliation_Seeking",
        "Social_Shared_Experience_Seeking": "Social_Affiliation_Seeking",
        
        # ----- Social/Intimacy Cluster -----
        "Social_Intimacy_Restoration": "Social_Intimacy_Seeking",
        "Social_Intimacy_Expression": "Social_Intimacy_Seeking",
        "Social_Intimacy_Acceptance": "Social_Intimacy_Seeking",
        "Belonging_Intimacy_Restoration": "Social_Intimacy_Seeking",
        
        # ----- Social/Support Cluster -----
        "Social_Support_Provision": "Social_Support_Exchange",
        "Social_Support_Seeking": "Social_Support_Exchange",
        "Social_Caregiving_Provision": "Social_Support_Exchange",
        "Social_Empathy_Elicitation": "Social_Support_Exchange",
        
        # ----- Social/Conflict Cluster -----
        "Social_Conflict_Avoidance": "Social_Conflict_Avoidance",
        "Safety_Conflict_Avoidance": "Social_Conflict_Avoidance",
        "Social_Tension_Reduction": "Social_Conflict_Avoidance",
        "Social_Resolution_Seeking": "Social_Conflict_Resolution",
        "Social_Relationship_Salvage": "Social_Conflict_Resolution",
        "Belonging_Forgiveness_Seeking": "Social_Conflict_Resolution",
        
        # ----- Social/Autonomy Cluster -----
        "Social_Autonomy_Seeking": "Social_Autonomy_Seeking",
        "Social_Relationship_Termination": "Social_Autonomy_Seeking",
        
        # ----- Social/Norm Cluster -----
        "Social_Norm_Enforcement": "Social_Norm_Compliance",
        "Social_Compliance_Seeking": "Social_Norm_Compliance",
        "Social_Modesty_Maintenance": "Social_Norm_Compliance",
        
        # ----- Safety Cluster -----
        "Safety_Threat_Avoidance": "Safety_Threat_Avoidance",
        "Safety_Threat_Neutralization": "Safety_Threat_Avoidance",
        "Safety_Threat_Management": "Safety_Threat_Avoidance",
        "Safety_Survival_Assurance_Seeking": "Safety_Threat_Avoidance",
        "Safety_Psychological_Protection": "Safety_Psychological_Protection",
        "Emotional_Vulnerability_Avoidance": "Safety_Psychological_Protection",
        "Safety_Resource_Protection": "Safety_Resource_Protection",
        
        # ----- Esteem/Competence Cluster -----
        "Esteem_Competence_Display": "Esteem_Competence_Display",
        "Esteem_Competence_Preservation": "Esteem_Competence_Display",
        "Esteem_SelfExpression_Seeking": "Esteem_SelfExpression_Seeking",
        
        # ----- Esteem/Status Cluster -----
        "Esteem_Status_Defense": "Esteem_Status_Assertion",
        "Esteem_Status_Differentiation": "Esteem_Status_Assertion",
        "Esteem_Dominance_Assertion": "Esteem_Status_Assertion",
        "Esteem_Superiority_Display": "Esteem_Status_Assertion",
        
        # ----- Esteem/Moral Cluster -----
        "Esteem_Moral_Integrity_Maintenance": "Esteem_Moral_Integrity",
        "Esteem_Moral_Assertion": "Esteem_Moral_Integrity",
        "Esteem_Reputation_Defense": "Esteem_Reputation_Defense",
        
        # ----- Epistemic Cluster -----
        "Epistemic_Information_Seeking": "Epistemic_Information_Seeking",
        "Epistemic_Information_Extraction": "Epistemic_Information_Seeking",
        "Epistemic_Explanation_Seeking": "Epistemic_Information_Seeking",
        "Epistemic_Uncertainty_Resolution": "Epistemic_Uncertainty_Resolution",
        "Epistemic_Discrepancy_Resolution": "Epistemic_Uncertainty_Resolution",
        "Epistemic_Certainty_Seeking": "Epistemic_Uncertainty_Resolution",
        "Epistemic_Truth_Verification": "Epistemic_Uncertainty_Resolution",
        "Epistemic_Causal_Attribution_Seeking": "Epistemic_Understanding_Seeking",
        "Epistemic_Social_Cue_Decoding": "Epistemic_Understanding_Seeking",
        "Epistemic_Exoneration_Seeking": "Epistemic_Exoneration_Seeking",
        
        # ----- Cognitive Cluster -----
        "Cognitive_Process_Optimization": "Cognitive_Efficiency_Seeking",
        "Cognitive_Effort_Minimization": "Cognitive_Efficiency_Seeking",
        "Cognitive_Efficiency_Maximization": "Cognitive_Efficiency_Seeking",
        
        # ----- Physiological Cluster -----
        "Physiological_Hygiene_Seeking": "Physiological_Comfort_Seeking",
        "Physiological_Rest_Seeking": "Physiological_Comfort_Seeking",
        "Physiological_Relief_Seeking": "Physiological_Comfort_Seeking",
        "Physiological_Noxious_Stimulus_Avoidance": "Physiological_Discomfort_Avoidance",
        
        # ----- Other -----
        "Social_Play_Engagement": "Social_Play_Engagement",
        "Social_Leisure_Participation": "Social_Play_Engagement",
        "Social_Stimulus_Avoidance": "Social_Stimulus_Avoidance",
        "Social_Bereavement_Processing": "Social_Bereavement_Processing",
        "Social_Understanding_Seeking": "Epistemic_Understanding_Seeking",
        "Social_Conflict_Simulation": "Social_Play_Engagement",
        "Social_Affective_State_Induction": "Social_Affective_Influence",
        "Social_Reciprocity_Maintenance": "Social_Reciprocity_Maintenance",
        "Social_Parental_Bonding_Seeking": "Social_Affiliation_Seeking",
        "Resource_Acquisition_Seeking": "Resource_Acquisition_Seeking",
    }
    
    # =========================================================================
    # EMOTION LABEL MAPPING
    # =========================================================================
    
    EMOTION_LABEL_MAP = {
        # Joy variants
        "Joy": "Joy",
        "Joy/Relief": "Joy",
        "Joy/Happiness": "Joy",
        "Joy/Amusement": "Joy",
        "Joy/Contentment": "Contentment",
        "Joy/Satisfaction": "Contentment",
        "Joy/Ecstasy": "Excitement",
        "Relief/Joy": "Joy",
        "Ecstasy/Joy": "Excitement",
        
        # Fear variants
        "Fear": "Fear",
        "Fear/Anxiety": "Fear",
        "Fear/Shock": "Fear",
        "Fear/Aggression": "Fear",
        "Anxiety": "Fear",
        "Apprehension": "Fear",
        "Anticipation/Anxiety": "Anxiety",
        
        # Anger variants
        "Anger": "Anger",
        "Anger/Stubbornness": "Anger",
        "Anger/Determination": "Anger",
        "Anger/Contempt": "Anger",
        "Frustration": "Anger",
        "Contempt": "Contempt",
        "Disgust": "Disgust",
        "Disgust/Relief": "Disgust",
        "Disgust/Pride": "Mixed",
        "Disapproval": "Contempt",
        
        # Sadness variants
        "Sadness": "Sadness",
        "Sadness/Resignation": "Sadness",
        "Sadness/Distress": "Sadness",
        "Sadness/Despair": "Sadness",
        "Resignation": "Sadness",
        "Resignation/Sadness": "Sadness",
        "Distress": "Sadness",
        "Desperation/Affection": "Mixed",
        
        # Surprise variants
        "Surprise": "Surprise",
        "Confusion/Surprise": "Surprise",
        "Shock/Defeat": "Surprise",
        
        # Neutral/Other
        "Contentment": "Contentment",
        "Contentment/Safety": "Contentment",
        "Excitement": "Excitement",
        "Excitement/Anticipation": "Excitement",
        "Anticipation": "Anticipation",
        "Interest": "Interest",
        "Interest/Anticipation": "Interest",
        "Amusement": "Joy",
        "Amusement (Nervous)": "Anxiety",
        "Embarrassment": "Embarrassment",
        "Embarrassment/Amusement": "Embarrassment",
        "Embarrassment/Nervousness": "Embarrassment",
        "Confusion": "Confusion",
        "Confusion/Annoyance": "Confusion",
        "Confusion/Concentration": "Confusion",
        "Boredom/Annoyance": "Boredom",
        "Neutral": "Neutral",
        "Neutral/Focused": "Neutral",
        "Neutral/Serious": "Neutral",
        "Skepticism": "Skepticism",
        "Contemplative/Judgmental": "Skepticism",
        "Guilt/Apprehension": "Guilt",
        "Nostalgia/Relief": "Nostalgia",
        "Hope": "Hope",
        "Pride": "Pride",
        "Confidence": "Confidence",
        "Determination": "Determination",
        "Concern": "Concern",
        "Tenderness": "Tenderness",
        "Supportive/Calm": "Contentment",
        "Exhaustion": "Exhaustion",
        "Politeness": "Neutral",
        "Hysteria/Mirth": "Excitement",
        "Serious/Authoritative": "Neutral",
        "Satisfaction": "Contentment",
        "Relief": "Relief",
        "Unknown": "Unknown",
        "Excitement (Manic)": "Excitement",
    }
    
    # =========================================================================
    # CANONICAL LABEL CATEGORIES
    # =========================================================================
    # After normalization, these are the expected canonical labels
    
    CANONICAL_DESIRE_CATEGORIES = {
        "Social": [
            "Social_Affiliation_Seeking",
            "Social_Intimacy_Seeking", 
            "Social_Support_Exchange",
            "Social_Conflict_Avoidance",
            "Social_Conflict_Resolution",
            "Social_Autonomy_Seeking",
            "Social_Norm_Compliance",
            "Social_Play_Engagement",
            "Social_Bereavement_Processing",
            "Social_Stimulus_Avoidance",
            "Social_Affective_Influence",
            "Social_Reciprocity_Maintenance",
        ],
        "Safety": [
            "Safety_Threat_Avoidance",
            "Safety_Psychological_Protection",
            "Safety_Resource_Protection",
        ],
        "Esteem": [
            "Esteem_Competence_Display",
            "Esteem_SelfExpression_Seeking",
            "Esteem_Status_Assertion",
            "Esteem_Moral_Integrity",
            "Esteem_Reputation_Defense",
        ],
        "Epistemic": [
            "Epistemic_Information_Seeking",
            "Epistemic_Uncertainty_Resolution",
            "Epistemic_Understanding_Seeking",
            "Epistemic_Exoneration_Seeking",
        ],
        "Cognitive": [
            "Cognitive_Efficiency_Seeking",
        ],
        "Physiological": [
            "Physiological_Comfort_Seeking",
            "Physiological_Discomfort_Avoidance",
        ],
        "Resource": [
            "Resource_Acquisition_Seeking",
        ],
    }
    
    def __init__(self):
        self.stats = {
            "files_processed": 0,
            "labels_normalized": 0,
            "emotions_normalized": 0,
            "unknown_labels": [],
            "unknown_emotions": [],
        }
    
    def normalize_desire_label(self, label: str) -> str:
        """Normalize a desire label to its canonical form."""
        if label in self.DESIRE_LABEL_MAP:
            return self.DESIRE_LABEL_MAP[label]
        else:
            # Keep original but log it
            if label not in self.stats["unknown_labels"]:
                self.stats["unknown_labels"].append(label)
            return label
    
    def normalize_emotion_label(self, label: str) -> str:
        """Normalize an emotion label to its canonical form."""
        if label in self.EMOTION_LABEL_MAP:
            return self.EMOTION_LABEL_MAP[label]
        else:
            if label not in self.stats["unknown_emotions"]:
                self.stats["unknown_emotions"].append(label)
            return label
    
    def normalize_annotation(self, anno: Dict) -> Dict:
        """Normalize all labels in an annotation."""
        result = deepcopy(anno)
        
        # Normalize desire_motivation_analysis
        for desire in result.get("desire_motivation_analysis", []):
            original = desire.get("desire_label", "")
            normalized = self.normalize_desire_label(original)
            if original != normalized:
                desire["desire_label"] = normalized
                desire["original_label"] = original  # Keep original for reference
                self.stats["labels_normalized"] += 1
        
        # Normalize desire_transitions
        for trans in result.get("desire_transitions", []):
            for key in ["desire_before", "desire_after"]:
                if key in trans and "label" in trans[key]:
                    original = trans[key]["label"]
                    normalized = self.normalize_desire_label(original)
                    if original != normalized:
                        trans[key]["label"] = normalized
                        trans[key]["original_label"] = original
        
        # Normalize character emotion states
        for char in result.get("characters", []):
            for state_key in ["initial_state", "final_state"]:
                if state_key in char:
                    emotion_state = char[state_key].get("emotional_state", {})
                    if "primary_emotion" in emotion_state:
                        original = emotion_state["primary_emotion"]
                        normalized = self.normalize_emotion_label(original)
                        if original != normalized:
                            emotion_state["primary_emotion"] = normalized
                            emotion_state["original_emotion"] = original
                            self.stats["emotions_normalized"] += 1
        
        # Add normalization metadata
        if "annotation_metadata" not in result:
            result["annotation_metadata"] = {}
        result["annotation_metadata"]["labels_normalized"] = True
        result["annotation_metadata"]["normalization_version"] = "1.0"
        
        return result
    
    def process_directory(
        self, 
        input_dir: str, 
        output_dir: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict:
        """Process all annotation files in a directory."""
        input_path = Path(input_dir)
        
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = input_path
        
        json_files = list(input_path.glob("*.json"))
        json_files = [f for f in json_files if not f.name.startswith("stats_") 
                      and f.name != "annotation_errors.json"]
        
        print(f"📂 Processing {len(json_files)} files from {input_dir}")
        
        for file_path in sorted(json_files):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    anno = json.load(f)
                
                normalized = self.normalize_annotation(anno)
                self.stats["files_processed"] += 1
                
                if not dry_run:
                    out_file = output_path / file_path.name
                    with open(out_file, 'w', encoding='utf-8') as f:
                        json.dump(normalized, f, ensure_ascii=False, indent=2)
                
            except Exception as e:
                print(f"⚠️  Error processing {file_path.name}: {e}")
        
        return self.stats
    
    def print_report(self):
        """Print normalization report."""
        print("\n" + "=" * 60)
        print("📊 LABEL NORMALIZATION REPORT")
        print("=" * 60)
        print(f"   Files processed: {self.stats['files_processed']}")
        print(f"   Desire labels normalized: {self.stats['labels_normalized']}")
        print(f"   Emotion labels normalized: {self.stats['emotions_normalized']}")
        
        if self.stats["unknown_labels"]:
            print(f"\n⚠️  Unknown desire labels (kept as-is):")
            for label in self.stats["unknown_labels"]:
                print(f"      - {label}")
        
        if self.stats["unknown_emotions"]:
            print(f"\n⚠️  Unknown emotion labels (kept as-is):")
            for label in self.stats["unknown_emotions"]:
                print(f"      - {label}")
        
        print("\n" + "=" * 60)
    
    def get_canonical_label_count(self) -> int:
        """Return the number of canonical desire labels."""
        count = 0
        for category, labels in self.CANONICAL_DESIRE_CATEGORIES.items():
            count += len(labels)
        return count


def main():
    parser = argparse.ArgumentParser(
        description="Normalize desire and emotion labels in annotations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview changes without modifying files
  python label_normalizer.py --input-dir data/annotations_test --dry-run
  
  # Normalize and save to new directory
  python label_normalizer.py --input-dir data/annotations_test --output-dir data/annotations_normalized
  
  # Normalize in place (overwrites original files)
  python label_normalizer.py --input-dir data/annotations_test --in-place
        """
    )
    
    parser.add_argument(
        "--input-dir", "-i",
        type=str,
        default=None,
        help="Directory containing annotation JSON files"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default=None,
        help="Output directory for normalized files (default: same as input)"
    )
    
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Modify files in place (use with caution)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing files"
    )
    
    parser.add_argument(
        "--show-mapping",
        action="store_true",
        help="Show the label mapping table"
    )
    
    args = parser.parse_args()
    
    normalizer = LabelNormalizer()
    
    if args.show_mapping:
        print("\n📋 DESIRE LABEL MAPPING")
        print("=" * 60)
        for original, canonical in sorted(normalizer.DESIRE_LABEL_MAP.items()):
            if original != canonical:
                print(f"   {original}")
                print(f"      → {canonical}")
        
        print(f"\n📊 Canonical labels: {normalizer.get_canonical_label_count()}")
        return
    
    if not args.input_dir:
        print("❌ Please specify --input-dir")
        return 1
    
    # Determine output directory
    if args.in_place:
        output_dir = args.input_dir
    else:
        output_dir = args.output_dir
    
    if not args.dry_run and not output_dir:
        print("❌ Please specify --output-dir or use --in-place")
        return 1
    
    # Process files
    normalizer.process_directory(
        input_dir=args.input_dir,
        output_dir=output_dir,
        dry_run=args.dry_run
    )
    
    normalizer.print_report()
    
    if args.dry_run:
        print("\n💡 This was a dry run. No files were modified.")
    elif output_dir:
        print(f"\n✅ Normalized files saved to: {output_dir}")


if __name__ == "__main__":
    main()