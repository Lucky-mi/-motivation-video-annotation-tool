#!/usr/bin/env python3
"""
Desire-VQA Annotation Statistics & Quality Analysis
====================================================
Analyzes annotation outputs to assess quality and consistency.

Usage:
    python annotation_stats.py --input-dir data/annotations_test
    python annotation_stats.py --input-dir data/annotations_test --output report.json --verbose
"""

import json
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import re


@dataclass
class AnnotationStats:
    """Statistics for a collection of annotations."""
    
    # Basic counts
    total_videos: int = 0
    total_characters: int = 0
    total_desire_analyses: int = 0
    total_transitions: int = 0
    total_behavioral_sequences: int = 0
    total_qa_segments: int = 0
    
    # Averages per video
    avg_characters_per_video: float = 0.0
    avg_desires_per_video: float = 0.0
    avg_transitions_per_video: float = 0.0
    avg_duration_seconds: float = 0.0
    
    # Label distributions
    desire_labels: Dict[str, int] = field(default_factory=dict)
    maslow_levels: Dict[str, int] = field(default_factory=dict)
    desire_types: Dict[str, int] = field(default_factory=dict)
    transition_types: Dict[str, int] = field(default_factory=dict)
    emotion_labels: Dict[str, int] = field(default_factory=dict)
    
    # Evidence analysis
    evidence_modality: Dict[str, int] = field(default_factory=dict)
    behavior_categories: Dict[str, int] = field(default_factory=dict)
    verbal_vs_nonverbal_ratio: float = 0.0
    
    # Confidence distribution
    confidence_levels: Dict[str, int] = field(default_factory=dict)
    
    # Quality flags
    videos_with_quality_issues: int = 0
    videos_with_occlusion: int = 0
    videos_with_ambiguous_behaviors: int = 0
    
    # Potential issues
    issues: List[str] = field(default_factory=list)


class AnnotationAnalyzer:
    """Analyzes annotation JSON files for statistics and quality assessment."""
    
    # Keywords indicating verbal/audio evidence
    VERBAL_KEYWORDS = [
        'verbal', 'says', 'said', 'saying', 'speaks', 'spoken', 'speech',
        'voice', 'vocal', 'tone', 'shout', 'yell', 'scream', 'whisper',
        'ask', 'question', 'answer', 'statement', 'exclaim', 'declare',
        'chant', 'sing', 'word', 'phrase', 'dialogue', 'conversation',
        'interrupts', 'replies', 'responds'
    ]
    
    # Keywords indicating visual/non-verbal evidence
    NONVERBAL_KEYWORDS = [
        'facial', 'expression', 'eyebrow', 'eye', 'gaze', 'look', 'stare',
        'smile', 'frown', 'grimace', 'jaw', 'mouth', 'lip',
        'posture', 'body', 'gesture', 'hand', 'arm', 'shoulder', 'head',
        'movement', 'motion', 'turn', 'lean', 'shift', 'recoil', 'freeze',
        'tension', 'relax', 'clench', 'grip', 'touch',
        'sweat', 'breathing', 'trembl', 'shiver', 'flush'
    ]
    
    def __init__(self, input_dir: str, verbose: bool = False):
        self.input_dir = Path(input_dir)
        self.verbose = verbose
        self.annotations: List[Dict] = []
        self.stats = AnnotationStats()
        
    def load_annotations(self) -> int:
        """Load all JSON annotation files."""
        json_files = list(self.input_dir.glob("*.json"))
        # Exclude error logs and raw files
        json_files = [f for f in json_files if not f.name.endswith('_raw.txt') 
                      and f.name != 'annotation_errors.json']
        
        for file_path in sorted(json_files):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['_source_file'] = file_path.name
                    self.annotations.append(data)
            except json.JSONDecodeError as e:
                print(f"⚠️  Failed to parse {file_path.name}: {e}")
            except Exception as e:
                print(f"⚠️  Error loading {file_path.name}: {e}")
        
        return len(self.annotations)
    
    def classify_evidence(self, text: str) -> str:
        """Classify evidence as verbal, nonverbal, or mixed."""
        text_lower = text.lower()
        
        has_verbal = any(kw in text_lower for kw in self.VERBAL_KEYWORDS)
        has_nonverbal = any(kw in text_lower for kw in self.NONVERBAL_KEYWORDS)
        
        if has_verbal and has_nonverbal:
            return 'mixed'
        elif has_verbal:
            return 'verbal'
        elif has_nonverbal:
            return 'nonverbal'
        else:
            return 'unclear'
    
    def extract_label_category(self, label: str) -> str:
        """Extract the category prefix from a desire label."""
        if '_' in label:
            return label.split('_')[0]
        return label
    
    def analyze(self) -> AnnotationStats:
        """Run full analysis on loaded annotations."""
        if not self.annotations:
            print("No annotations loaded!")
            return self.stats
        
        # Counters
        desire_labels = Counter()
        maslow_levels = Counter()
        desire_types = Counter()
        transition_types = Counter()
        emotion_labels = Counter()
        behavior_categories = Counter()
        evidence_modality = Counter()
        confidence_levels = Counter()
        
        total_durations = []
        characters_per_video = []
        desires_per_video = []
        transitions_per_video = []
        
        for anno in self.annotations:
            video_id = anno.get('video_id', 'unknown')
            
            # Duration
            duration = anno.get('duration_seconds', 0)
            if duration:
                total_durations.append(duration)
            
            # Characters
            characters = anno.get('characters', [])
            self.stats.total_characters += len(characters)
            characters_per_video.append(len(characters))
            
            # Extract emotions from character states
            for char in characters:
                for state_key in ['initial_state', 'final_state']:
                    state = char.get(state_key, {})
                    emotion_state = state.get('emotional_state', {})
                    emotion = emotion_state.get('primary_emotion')
                    if emotion:
                        emotion_labels[emotion] += 1
            
            # Desire/Motivation Analysis
            desire_analyses = anno.get('desire_motivation_analysis', [])
            self.stats.total_desire_analyses += len(desire_analyses)
            desires_per_video.append(len(desire_analyses))
            
            for desire in desire_analyses:
                # Labels
                label = desire.get('desire_label', 'Unknown')
                desire_labels[label] += 1
                
                # Maslow level
                maslow = desire.get('maslow_level', 'unknown')
                maslow_levels[maslow] += 1
                
                # Desire type
                dtype = desire.get('desire_type', 'unknown')
                desire_types[dtype] += 1
                
                # Confidence
                conf = desire.get('confidence', 'unknown')
                confidence_levels[conf] += 1
                
                # Evidence modality analysis
                for evidence in desire.get('supporting_evidence', []):
                    desc = evidence.get('description', '')
                    btype = evidence.get('behavior_type', '')
                    modality = self.classify_evidence(f"{btype} {desc}")
                    evidence_modality[modality] += 1
            
            # Transitions
            transitions = anno.get('desire_transitions', [])
            self.stats.total_transitions += len(transitions)
            transitions_per_video.append(len(transitions))
            
            for trans in transitions:
                ttype = trans.get('transition_type', 'unknown')
                transition_types[ttype] += 1
            
            # Behavioral Sequence
            behaviors = anno.get('behavioral_sequence', [])
            self.stats.total_behavioral_sequences += len(behaviors)
            
            for behavior in behaviors:
                cat = behavior.get('behavior_category', 'unknown')
                behavior_categories[cat] += 1
                
                # Check description modality
                desc = behavior.get('behavior_description', '')
                modality = self.classify_evidence(desc)
                evidence_modality[modality] += 1
            
            # QA Segments
            qa_segs = anno.get('key_segments_for_qa', [])
            self.stats.total_qa_segments += len(qa_segs)
            
            # Quality flags
            metadata = anno.get('annotation_metadata', {})
            quality_flags = metadata.get('quality_flags', {})
            
            if quality_flags.get('video_quality_issues'):
                self.stats.videos_with_quality_issues += 1
            if quality_flags.get('occlusion_present'):
                self.stats.videos_with_occlusion += 1
            if quality_flags.get('ambiguous_behaviors'):
                self.stats.videos_with_ambiguous_behaviors += 1
        
        # Populate stats
        self.stats.total_videos = len(self.annotations)
        
        # Averages
        if self.stats.total_videos > 0:
            self.stats.avg_characters_per_video = sum(characters_per_video) / len(characters_per_video)
            self.stats.avg_desires_per_video = sum(desires_per_video) / len(desires_per_video)
            self.stats.avg_transitions_per_video = sum(transitions_per_video) / len(transitions_per_video)
        
        if total_durations:
            self.stats.avg_duration_seconds = sum(total_durations) / len(total_durations)
        
        # Convert counters to dicts
        self.stats.desire_labels = dict(desire_labels.most_common())
        self.stats.maslow_levels = dict(maslow_levels.most_common())
        self.stats.desire_types = dict(desire_types.most_common())
        self.stats.transition_types = dict(transition_types.most_common())
        self.stats.emotion_labels = dict(emotion_labels.most_common())
        self.stats.behavior_categories = dict(behavior_categories.most_common())
        self.stats.evidence_modality = dict(evidence_modality.most_common())
        self.stats.confidence_levels = dict(confidence_levels.most_common())
        
        # Calculate verbal vs nonverbal ratio
        verbal_count = evidence_modality.get('verbal', 0)
        nonverbal_count = evidence_modality.get('nonverbal', 0)
        mixed_count = evidence_modality.get('mixed', 0)
        total_evidence = verbal_count + nonverbal_count + mixed_count
        
        if total_evidence > 0:
            self.stats.verbal_vs_nonverbal_ratio = verbal_count / total_evidence
        
        # Identify potential issues
        self._identify_issues()
        
        return self.stats
    
    def _identify_issues(self):
        """Identify potential quality issues in the annotations."""
        issues = []
        
        # Too many unique labels
        unique_labels = len(self.stats.desire_labels)
        if unique_labels > 50:
            issues.append(f"⚠️  High label diversity: {unique_labels} unique desire labels (may need clustering)")
        
        # Too much verbal evidence
        if self.stats.verbal_vs_nonverbal_ratio > 0.5:
            pct = self.stats.verbal_vs_nonverbal_ratio * 100
            issues.append(f"⚠️  High verbal evidence ratio: {pct:.1f}% (consider strengthening non-verbal focus)")
        
        # Low transition detection
        if self.stats.avg_transitions_per_video < 0.5:
            issues.append(f"⚠️  Low transition detection: avg {self.stats.avg_transitions_per_video:.2f} per video")
        
        # Maslow distribution check
        maslow_counts = self.stats.maslow_levels
        total_maslow = sum(maslow_counts.values())
        if total_maslow > 0:
            high_level_pct = (maslow_counts.get('esteem', 0) + maslow_counts.get('self_actualization', 0)) / total_maslow
            if high_level_pct > 0.4:
                issues.append(f"⚠️  High-level Maslow over-representation: {high_level_pct*100:.1f}% (check parsimony principle)")
        
        # Confidence distribution
        conf_counts = self.stats.confidence_levels
        total_conf = sum(conf_counts.values())
        if total_conf > 0:
            low_conf_pct = conf_counts.get('low', 0) / total_conf
            if low_conf_pct > 0.3:
                issues.append(f"⚠️  High uncertainty: {low_conf_pct*100:.1f}% low confidence ratings")
        
        self.stats.issues = issues
    
    def print_report(self):
        """Print a formatted report to console."""
        s = self.stats
        
        print("\n" + "=" * 70)
        print("📊 DESIRE-VQA ANNOTATION STATISTICS REPORT")
        print("=" * 70)
        
        # Overview
        print("\n📁 OVERVIEW")
        print("-" * 40)
        print(f"   Total videos analyzed: {s.total_videos}")
        print(f"   Total characters: {s.total_characters}")
        print(f"   Total desire analyses: {s.total_desire_analyses}")
        print(f"   Total transitions: {s.total_transitions}")
        print(f"   Total QA segments: {s.total_qa_segments}")
        
        # Averages
        print("\n📈 AVERAGES PER VIDEO")
        print("-" * 40)
        print(f"   Duration: {s.avg_duration_seconds:.1f} seconds")
        print(f"   Characters: {s.avg_characters_per_video:.2f}")
        print(f"   Desire analyses: {s.avg_desires_per_video:.2f}")
        print(f"   Transitions: {s.avg_transitions_per_video:.2f}")
        
        # Desire Labels
        print("\n🏷️  DESIRE LABEL DISTRIBUTION")
        print("-" * 40)
        print(f"   Unique labels: {len(s.desire_labels)}")
        print("\n   Top 15 labels:")
        for i, (label, count) in enumerate(list(s.desire_labels.items())[:15], 1):
            print(f"   {i:2d}. {label}: {count}")
        
        # Label Categories
        print("\n📂 LABEL CATEGORIES (Prefix Analysis)")
        print("-" * 40)
        category_counts = Counter()
        for label in s.desire_labels:
            cat = label.split('_')[0] if '_' in label else label
            category_counts[cat] += s.desire_labels[label]
        for cat, count in category_counts.most_common():
            pct = count / sum(category_counts.values()) * 100
            print(f"   {cat}: {count} ({pct:.1f}%)")
        
        # Maslow Levels
        print("\n🔺 MASLOW HIERARCHY DISTRIBUTION")
        print("-" * 40)
        maslow_order = ['physiological', 'safety', 'belonging', 'esteem', 'self_actualization']
        total_maslow = sum(s.maslow_levels.values())
        for level in maslow_order:
            count = s.maslow_levels.get(level, 0)
            pct = (count / total_maslow * 100) if total_maslow > 0 else 0
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            print(f"   {level:20s}: {bar} {count:3d} ({pct:5.1f}%)")
        
        # Transition Types
        print("\n🔄 TRANSITION TYPE DISTRIBUTION")
        print("-" * 40)
        for ttype, count in s.transition_types.items():
            print(f"   {ttype}: {count}")
        
        # Evidence Modality
        print("\n🎯 EVIDENCE MODALITY ANALYSIS")
        print("-" * 40)
        total_evidence = sum(s.evidence_modality.values())
        for modality, count in s.evidence_modality.items():
            pct = (count / total_evidence * 100) if total_evidence > 0 else 0
            print(f"   {modality:12s}: {count:4d} ({pct:5.1f}%)")
        print(f"\n   ⚡ Verbal/Total Ratio: {s.verbal_vs_nonverbal_ratio*100:.1f}%")
        
        # Behavior Categories
        print("\n👁️  BEHAVIOR CATEGORY DISTRIBUTION")
        print("-" * 40)
        for cat, count in s.behavior_categories.items():
            print(f"   {cat}: {count}")
        
        # Emotions
        print("\n😊 EMOTION DISTRIBUTION (from character states)")
        print("-" * 40)
        for emotion, count in list(s.emotion_labels.items())[:10]:
            print(f"   {emotion}: {count}")
        
        # Confidence
        print("\n✅ CONFIDENCE LEVEL DISTRIBUTION")
        print("-" * 40)
        for level, count in s.confidence_levels.items():
            pct = (count / sum(s.confidence_levels.values()) * 100) if s.confidence_levels else 0
            print(f"   {level}: {count} ({pct:.1f}%)")
        
        # Quality Flags
        print("\n🚩 QUALITY FLAGS")
        print("-" * 40)
        print(f"   Videos with quality issues: {s.videos_with_quality_issues}")
        print(f"   Videos with occlusion: {s.videos_with_occlusion}")
        print(f"   Videos with ambiguous behaviors: {s.videos_with_ambiguous_behaviors}")
        
        # Issues
        if s.issues:
            print("\n⚠️  POTENTIAL ISSUES DETECTED")
            print("-" * 40)
            for issue in s.issues:
                print(f"   {issue}")
        else:
            print("\n✅ No major issues detected!")
        
        print("\n" + "=" * 70)
    
    def save_report(self, output_path: str):
        """Save statistics to JSON file."""
        output_path = Path(output_path)
        
        report = {
            "summary": {
                "total_videos": self.stats.total_videos,
                "total_characters": self.stats.total_characters,
                "total_desire_analyses": self.stats.total_desire_analyses,
                "total_transitions": self.stats.total_transitions,
                "unique_desire_labels": len(self.stats.desire_labels),
                "verbal_evidence_ratio": self.stats.verbal_vs_nonverbal_ratio
            },
            "averages": {
                "duration_seconds": self.stats.avg_duration_seconds,
                "characters_per_video": self.stats.avg_characters_per_video,
                "desires_per_video": self.stats.avg_desires_per_video,
                "transitions_per_video": self.stats.avg_transitions_per_video
            },
            "distributions": {
                "desire_labels": self.stats.desire_labels,
                "maslow_levels": self.stats.maslow_levels,
                "desire_types": self.stats.desire_types,
                "transition_types": self.stats.transition_types,
                "emotion_labels": self.stats.emotion_labels,
                "behavior_categories": self.stats.behavior_categories,
                "evidence_modality": self.stats.evidence_modality,
                "confidence_levels": self.stats.confidence_levels
            },
            "quality": {
                "videos_with_quality_issues": self.stats.videos_with_quality_issues,
                "videos_with_occlusion": self.stats.videos_with_occlusion,
                "videos_with_ambiguous_behaviors": self.stats.videos_with_ambiguous_behaviors
            },
            "issues": self.stats.issues
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Desire-VQA annotation statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic analysis
  python annotation_stats.py --input-dir data/annotations_test
  
  # Save report to file
  python annotation_stats.py --input-dir data/annotations_test --output stats_report.json
  
  # Verbose mode (show per-video details)
  python annotation_stats.py --input-dir data/annotations_test --verbose
        """
    )
    
    parser.add_argument(
        "--input-dir", "-i",
        type=str,
        default="data/annotations_test",
        help="Directory containing annotation JSON files"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output path for JSON report (optional)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output"
    )
    
    args = parser.parse_args()
    
    # Check input directory
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        return 1
    
    # Run analysis
    analyzer = AnnotationAnalyzer(args.input_dir, verbose=args.verbose)
    
    print(f"📂 Loading annotations from: {args.input_dir}")
    count = analyzer.load_annotations()
    print(f"✅ Loaded {count} annotation files")
    
    if count == 0:
        print("❌ No valid annotation files found!")
        return 1
    
    print("🔍 Analyzing...")
    analyzer.analyze()
    
    # Print report
    analyzer.print_report()
    
    # Save if requested
    if args.output:
        analyzer.save_report(args.output)
    
    return 0


if __name__ == "__main__":
    exit(main())