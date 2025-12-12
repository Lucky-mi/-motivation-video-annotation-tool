# backend/annotation_schema_v3.py
"""
视频标注Schema V3 - 属性动态 + 开放式心理推断
保留完整视频（带音频），用于后续视觉/多模态实验
"""
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field


class AttributeChange(BaseModel):
    """属性变化 - 描述人物属性的上升/下降"""
    attribute_name: str = Field(..., description="属性名称，如：愤怒程度、信任度、焦虑水平、警惕性等")
    direction: Literal["上升", "下降", "保持", "波动"] = Field(..., description="变化方向")
    start_level: Optional[Literal["高", "中", "低"]] = Field(None, description="起始水平（如果能判断）")
    end_level: Optional[Literal["高", "中", "低"]] = Field(None, description="结束水平（如果能判断）")
    evidence: List[str] = Field(..., description="可观察的证据（表情、动作、语气、行为）")
    confidence: Literal["高", "中", "低"] = Field(..., description="判断的确定性")


class CharacterDescription(BaseModel):
    """人物描述"""
    character_id: str = Field(..., description="人物标识，如 A, B, C 或描述性名称")
    appearance: str = Field(..., description="外观描述（年龄、性别、衣着、特征等）")
    initial_state: str = Field(..., description="初始状态（情绪、姿态、位置）")
    final_state: str = Field(..., description="最终状态（情绪、姿态、位置）")
    role_in_interaction: str = Field(..., description="在互动中的角色（发起者、回应者、旁观者等）")
    attribute_changes: List[AttributeChange] = Field(
        default_factory=list,
        description="属性变化列表"
    )


class SceneDescription(BaseModel):
    """场景描述"""
    location: str = Field(..., description="地点（室内/室外，具体场所）")
    time_period: Optional[str] = Field(None, description="时间段（如果能判断：白天/夜晚/特定时间）")
    atmosphere: str = Field(..., description="氛围（紧张、轻松、冲突、亲密等）")
    social_context: str = Field(..., description="社交情境（公开场合、私密空间、工作场所等）")
    key_objects: List[str] = Field(default_factory=list, description="关键物品或环境要素")


class ObservableBehavior(BaseModel):
    """可观察的行为"""
    timestamp: str = Field(..., description="时间戳或时间段，如 '0:05-0:10' 或 '开始阶段'")
    character_id: str = Field(..., description="执行行为的人物")
    behavior_category: Literal[
        "表情变化", "肢体动作", "眼神交流", "语气变化",
        "身体距离", "触碰/回避", "姿态变化", "对话内容", "其他"
    ] = Field(..., description="行为类别")
    detailed_description: str = Field(..., description="行为的详细描述（越具体越好）")
    intensity: Literal["强", "中", "弱"] = Field(..., description="强度或显著性")
    target: Optional[str] = Field(None, description="行为的对象（如果是互动行为）")


class PsychologyReference(BaseModel):
    """心理学知识参考"""
    concept: str = Field(..., description="心理学概念名称")
    description: str = Field(..., description="概念的简要说明")
    relevance: str = Field(..., description="与当前视频场景的相关性")


class OpenInference(BaseModel):
    """开放式推断 - 模型自己的解读，不用固定标签"""
    inference_aspect: str = Field(
        ...,
        description="推断的方面（如：人物A的真实意图、人物B对A的看法、情境中的隐藏信息等）"
    )
    reasoning_process: str = Field(
        ...,
        description="推理过程的详细描述（怎么得出这个推断的）"
    )
    supporting_evidence: List[str] = Field(
        ...,
        description="支持该推断的具体证据（行为、表情、语气、情境等）"
    )
    conclusion: str = Field(..., description="推断结论（开放式描述，不用固定标签）")
    confidence: Literal["高", "中", "低"] = Field(..., description="推断的确定性")
    alternative_interpretations: List[str] = Field(
        default_factory=list,
        description="其他可能的解释（承认推断的不确定性）"
    )
    psychology_concepts_applied: List[str] = Field(
        default_factory=list,
        description="应用的心理学概念（如果有）"
    )


class VideoAnnotationV3(BaseModel):
    """完整的视频标注 V3 - 简化版"""
    video_id: str = Field(..., description="视频唯一标识")
    video_path: str = Field(..., description="视频文件路径（带音频）")
    duration: float = Field(..., description="视频时长（秒）")

    # 视频质量信息
    is_clean_video: bool = Field(
        ...,
        description="是否为纯净视频（无字幕、无特效、无水印等后期加工）"
    )
    quality_notes: Optional[str] = Field(
        None,
        description="视频质量的额外说明（如有少量水印等）"
    )

    # 场景和人物
    scene: SceneDescription = Field(..., description="场景描述")
    characters: List[CharacterDescription] = Field(..., description="人物描述列表")

    # 行为序列
    observable_behaviors: List[ObservableBehavior] = Field(
        ...,
        description="可观察的行为序列（按时间顺序）"
    )

    # 开放式推断（核心！）
    open_inferences: List[OpenInference] = Field(
        ...,
        description="模型的开放式推断（不使用固定标签）"
    )

    # 心理学知识参考（供标注参考，不强制使用）
    relevant_psychology: List[PsychologyReference] = Field(
        default_factory=list,
        description="相关的心理学知识（仅供参考）"
    )

    # 元数据
    annotator_id: Optional[str] = Field(None, description="标注者ID")
    annotation_time: str = Field(..., description="标注时间")
    annotation_model: Optional[str] = Field(None, description="使用的AI模型")


# 简化的标注提示模板
ANNOTATION_PROMPT_V3 = """
你是一位心理学研究专家，需要对视频进行Theory of Mind（心智理论）标注。

# 标注任务

## 1. 场景描述
- 地点和环境
- 社交情境
- 氛围
- 关键物品

## 2. 人物描述
为每个主要人物创建描述：
- 外观特征
- 初始状态和最终状态
- 在互动中的角色
- **属性变化**（重要！）：
  * 识别可观察的属性（如：愤怒程度、焦虑水平、信任度、警惕性、自信心等）
  * 说明变化方向：上升/下降/保持/波动
  * 提供具体的行为证据（表情、动作、语气、肢体语言）

示例：
```
属性：焦虑水平
方向：上升
起始：中等
结束：高
证据：
- 语速逐渐加快
- 手开始不停摆弄物品
- 眉头紧锁
- 身体前倾，显得紧张
确定性：高
```

## 3. 行为序列
按时间顺序记录关键行为：
- 表情变化
- 肢体动作
- 眼神交流
- 语气和对话
- 身体距离变化
- 任何显著的互动

## 4. 开放式推断（核心！）
**不要使用固定的标签或类别**，而是进行开放式根据主流心理学知识的心理推断：

### 推断步骤：
1. **选择推断方面**：
   - 人物的真实意图（说的和想的是否一致？）
   - 人物的情感状态（不仅是"愤怒"，而是为什么愤怒？愤怒中混合了什么？）
   - 人物对他人的看法
   - 人物的信念或假设
   - 人物的desire/motivation（标注核心，需要根据提供的主流心理学知识自行推断标签）
   - 情境中的隐藏信息

2. **详细描述推理过程**：
   - 我注意到...（观察）
   - 这可能意味着...（初步推断）
   - 因为...（支持证据）
   - 因此我认为...（结论）

3. **列出所有支持证据**：
   - 具体的行为
   - 表情细节
   - 语气特点
   - 情境线索

4. **说明确定性和其他可能**：
   - 这个推断的确定性（高/中/低）
   - 还有哪些其他解释？

### 示例：
```
推断方面：人物A在对话中是否真诚

推理过程：
我注意到A在表达歉意时，虽然语言上说"很抱歉"，但：
1. 眼神多次向下或移开，缺乏直接的眼神接触
2. 肢体语言较为僵硬，缺乏开放性姿态
3. 语气相对平淡，缺少情感波动
4. 说完后快速转身离开，没有等待回应

这可能意味着A的道歉不是完全发自内心，或者：
- A可能感到尴尬而不是真正的悔意
- A可能是迫于压力而道歉
- A可能还在生气，只是表面上道歉

因此我认为：A的道歉可能更多是为了平息冲突而非真心悔过，内心可能还残留着不满或委屈。

支持证据：
- 眼神回避（典型的不舒适或不真诚信号）
- 僵硬的肢体语言（防御性姿态）
- 缺乏情感投入的语气
- 快速结束互动（逃避深入交流）

确定性：中等（因为也可能是A性格内向或不善表达）

其他可能：
- A可能确实感到抱歉，但由于尴尬而表现不自然
- A可能因为其他压力而情绪状态不佳，影响了表达
```

## 5. 心理学知识应用（可选）
以下心理学概念可能有帮助，但**不要直接作为标签使用**，而是作为推理的参考：

- 虚假信念：某人相信的与事实不符
- 意图隐藏：故意不表露真实意图
- 情绪调节：控制或改变自己的情绪
- 社会参照：通过观察他人来理解情境
- 情绪感染：情绪在人与人之间传播
- 归因偏差：对他人行为原因的推断偏见
- 去中心化：从他人视角理解事件
- 心智化：理解行为背后的心理状态

如果你的推断用到了这些概念，可以在标注中说明。

---

## 重要原则

1. ✅ **详细记录属性变化**（上升/下降）
2. ✅ **开放式描述，不用固定标签**
3. ✅ **提供充分的行为证据**
4. ✅ **说明推断的确定性**
5. ✅ **考虑多种可能的解释**
6. ✅ **关注言行一致性**

---

请严格按照 VideoAnnotationV3 的JSON Schema输出标注结果。
请尽量保持简洁明了，不要输出冗余的内容，保证json文件不要太长超过输出限制。
"""


# 心理学知识库
PSYCHOLOGY_KNOWLEDGE_BASE = [
    {
        "concept": "虚假信念 (False Belief)",
        "description": "某人相信的事情与客观事实不符，这是心智理论的核心能力",
        "key_indicators": [
            "基于错误信息的行为",
            "期待落空的反应",
            "解释他人看似奇怪的行为"
        ]
    },
    {
        "concept": "意图隐藏 (Intention Concealment)",
        "description": "个体故意不表露真实意图，可能出于礼貌、策略或欺骗",
        "key_indicators": [
            "言行不一",
            "微表情泄露",
            "语气和内容不匹配",
            "眼神回避或过度注视"
        ]
    },
    {
        "concept": "情绪调节 (Emotion Regulation)",
        "description": "个体控制、改变或维持自己情绪的过程",
        "key_indicators": [
            "深呼吸或自我安抚",
            "转移注意力",
            "表情抑制或强化",
            "改变身体姿态"
        ]
    },
    {
        "concept": "情绪感染 (Emotional Contagion)",
        "description": "一个人的情绪状态影响他人，导致情绪的传播",
        "key_indicators": [
            "模仿表情",
            "同步肢体语言",
            "情绪氛围的扩散"
        ]
    },
    {
        "concept": "社会参照 (Social Referencing)",
        "description": "通过观察他人反应来理解不确定情境，指导自己行为",
        "key_indicators": [
            "看向他人寻求线索",
            "模仿他人反应",
            "等待他人先行动"
        ]
    },
    {
        "concept": "归因偏差 (Attribution Bias)",
        "description": "对他人行为原因的推断可能受到偏见影响",
        "key_indicators": [
            "过度归因于性格而非情境",
            "自利性解释",
            "基本归因错误"
        ]
    },
    {
        "concept": "去中心化 (Decentering)",
        "description": "从他人视角理解事件，而非只从自己视角",
        "key_indicators": [
            "考虑他人感受",
            "调整行为以适应他人",
            "理解不同观点"
        ]
    },
    {
        "concept": "心智化 (Mentalization)",
        "description": "将他人行为理解为有心智状态（信念、欲望、情感）驱动的过程",
        "key_indicators": [
            "解释行为的心理原因",
            "预测他人反应",
            "调整互动策略"
        ]
    }
]
