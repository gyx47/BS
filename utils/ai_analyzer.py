"""
AI图片分析模块
支持多种AI服务：智谱AI、OpenAI Vision API、DeepSeek、Gemini、Google Vision API、本地模型等
"""
import os
import sys
import base64
import requests
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class AIAnalyzer:
    """AI图片分析器，支持多种后端服务"""
    
    def __init__(self):
        self.provider = os.getenv('AI_PROVIDER', 'fallback').lower()
        # 分别获取各个API的key
        self.zhipu_api_key = os.getenv('ZHIPU_API_KEY') or os.getenv('AI_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY') or os.getenv('AI_API_KEY')
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY') or os.getenv('AI_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY') or os.getenv('AI_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('AI_API_KEY')
        # 兼容旧代码
        self.api_key = self.zhipu_api_key or self.gemini_api_key or self.openai_api_key
        
        # 打印当前配置信息（仅在调试时）
        if os.getenv('DEBUG_AI_ANALYZER', '').lower() == 'true':
            print(f"[AI分析器] Provider: {self.provider}")
            print(f"[AI分析器] 检测到的API Keys: Zhipu={bool(self.zhipu_api_key)}, "
                  f"OpenAI={bool(self.openai_api_key)}, DeepSeek={bool(self.deepseek_api_key)}, "
                  f"Gemini={bool(self.gemini_api_key)}, Google={bool(self.google_api_key)}")
        
    def analyze(self, image_path: str) -> List[str]:
        """
        分析图片并返回标签列表
        按优先级尝试：智谱AI -> OpenAI -> DeepSeek -> Gemini -> Google Vision -> 本地模型 -> 回退方案
        """
        tags = []
        
        # 如果明确指定了provider，使用指定的provider
        if self.provider != 'fallback':
            if self.provider == 'zhipu' and self.zhipu_api_key:
                tags = self._analyze_with_zhipu(image_path)
            elif self.provider == 'openai' and self.openai_api_key:
                tags = self._analyze_with_openai(image_path)
            elif self.provider == 'deepseek' and self.deepseek_api_key:
                tags = self._analyze_with_deepseek(image_path)
            elif self.provider == 'gemini' and self.gemini_api_key:
                tags = self._analyze_with_gemini(image_path)
            elif self.provider == 'google' and self.google_api_key:
                tags = self._analyze_with_google_vision(image_path)
            elif self.provider == 'local':
                tags = self._analyze_with_local_model(image_path)
        else:
            # 如果provider是fallback或未设置，自动检测可用的API，优先使用智谱AI
            if self.zhipu_api_key:
                print("检测到智谱AI API Key，使用智谱AI进行分析...")
                tags = self._analyze_with_zhipu(image_path)
            elif self.openai_api_key:
                print("检测到OpenAI API Key，使用OpenAI进行分析...")
                tags = self._analyze_with_openai(image_path)
            elif self.deepseek_api_key:
                print("检测到DeepSeek API Key，使用DeepSeek进行分析...")
                tags = self._analyze_with_deepseek(image_path)
            elif self.gemini_api_key:
                print("检测到Gemini API Key，使用Gemini进行分析...")
                tags = self._analyze_with_gemini(image_path)
            elif self.google_api_key:
                print("检测到Google Vision API Key，使用Google Vision进行分析...")
                tags = self._analyze_with_google_vision(image_path)
            elif self.provider == 'local':
                tags = self._analyze_with_local_model(image_path)
            else:
                tags = self._fallback_analysis(image_path)
        
        # 对返回的标签进行顿号分割处理
        if tags:
            tags = split_tags_by_pause(tags)
        
        return tags
    
    def _analyze_with_openai(self, image_path: str) -> List[str]:
        """使用OpenAI Vision API分析图片"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.openai_api_key)
            
            # 读取图片并转换为base64
            with open(image_path, 'rb') as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 确定图片MIME类型
            import mimetypes
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type:
                mime_type = 'image/jpeg'
            
            # 调用OpenAI Vision API
            response = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "请分析这张图片的内容，用中文返回5-10个标签，用逗号分隔。标签应该包括：场景类型（如风景、城市、人物）、主要对象、颜色特征、情绪氛围等。只返回标签，不要其他文字。"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=150
            )
            
            # 解析返回的标签
            tags_text = response.choices[0].message.content.strip()
            tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
            return tags[:10]  # 限制最多10个标签
            
        except ImportError:
            print("OpenAI库未安装，请运行: pip install openai")
            return self._fallback_analysis(image_path)
        except Exception as e:
            print(f"OpenAI分析失败: {e}")
            return self._fallback_analysis(image_path)
    
    def _analyze_with_google_vision(self, image_path: str) -> List[str]:
        """使用Google Cloud Vision API分析图片"""
        try:
            from google.cloud import vision
            
            client = vision.ImageAnnotatorClient()
            
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # 执行标签检测
            response = client.label_detection(image=image)
            labels = response.label_annotations
            
            # 转换为中文标签（这里需要翻译，或使用中文API）
            tags = []
            label_mapping = {
                'landscape': '风景',
                'nature': '自然',
                'person': '人物',
                'building': '建筑',
                'city': '城市',
                'water': '水',
                'mountain': '山脉',
                'beach': '海滩',
                'sunset': '日落',
                'sunrise': '日出',
                'flower': '花朵',
                'tree': '树木',
                'animal': '动物',
                'portrait': '肖像',
                'street': '街道',
                'sky': '天空',
                'cloud': '云朵',
                'ocean': '海洋',
                'forest': '森林',
                'garden': '花园'
            }
            
            for label in labels[:10]:  # 取前10个标签
                label_name = label.description.lower()
                # 尝试映射到中文
                chinese_tag = label_mapping.get(label_name, label_name)
                if chinese_tag not in tags:
                    tags.append(chinese_tag)
            
            return tags if tags else self._fallback_analysis(image_path)
            
        except ImportError:
            print("Google Cloud Vision库未安装，请运行: pip install google-cloud-vision")
            return self._fallback_analysis(image_path)
        except Exception as e:
            print(f"Google Vision分析失败: {e}")
            return self._fallback_analysis(image_path)

    def _analyze_with_deepseek(self, image_path: str) -> List[str]:
        """使用DeepSeek API分析图片"""
        try:
            api_url = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
            model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
            timeout = int(os.getenv('DEEPSEEK_TIMEOUT', '60'))

            with open(image_path, 'rb') as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            prompt = (
                "你是一名中文图片标签助手。请阅读给出的图片Base64内容，"
                "结合你对图像的理解，用中文输出5~10个标签，"
                "覆盖场景、主体、颜色或情绪等信息。只输出逗号分隔的标签，不要多余文字。"
            )

            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "temperature": 0.2,
                "max_tokens": 200,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个可以解析图片Base64并生成中文标签的助手。"
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "input_image",
                                "image_base64": base64_image
                            }
                        ]
                    }
                ]
            }

            response = requests.post(api_url, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            choices = data.get('choices') or []
            if not choices:
                return self._fallback_analysis(image_path)

            content = choices[0].get('message', {}).get('content') or ""
            if isinstance(content, list):
                combined = []
                for part in content:
                    if isinstance(part, dict) and part.get('type') == 'output_text':
                        combined.append(part.get('text', ''))
                content = ''.join(combined)

            tags = [tag.strip() for tag in content.replace('，', ',').split(',') if tag.strip()]
            return tags[:10] if tags else self._fallback_analysis(image_path)

        except Exception as e:
            print(f"DeepSeek分析失败: {e}")
            return self._fallback_analysis(image_path)

    def _analyze_with_zhipu(self, image_path: str) -> List[str]:
        """使用智谱AI API分析图片，带重试和容错机制"""
        try:
            from zhipuai import ZhipuAI
            import mimetypes
            
            # 获取配置
            api_key = self.zhipu_api_key
            if not api_key:
                raise RuntimeError('ZHIPU_API_KEY 未配置')
            
            # 初始化客户端
            client = ZhipuAI(api_key=api_key)
            
            # 读取图片并转换为base64
            with open(image_path, 'rb') as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 确定图片MIME类型
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type:
                mime_type = 'image/jpeg'
            
            prompt = "请分析这张图片的内容，用中文返回5-10个标签，用逗号分隔。标签应该包括：场景类型（如风景、城市、人物）、主要对象、颜色特征、情绪氛围等。只返回标签，不要其他文字。"
            
            # 添加重试机制
            max_retries = 3
            base_delay = 1  # 基础延迟（秒）
            
            for attempt in range(max_retries):
                try:
                    # 调用智谱AI API（使用视觉模型）
                    # 智谱AI支持图片的格式：data:image/{mime_type};base64,{base64_image}
                    # 注意：如果glm-4v不可用，可以尝试glm-4-flash或其他视觉模型
                    model_name = os.getenv('ZHIPU_MODEL', 'glm-4v')  # 允许通过环境变量配置模型
                    
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": prompt
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{mime_type};base64,{base64_image}"
                                        }
                                    }
                                ]
                            }
                        ],
                        max_tokens=200,
                        temperature=0.2
                    )
                    
                    # 解析返回的标签
                    if response.choices and len(response.choices) > 0:
                        content = response.choices[0].message.content
                        if content:
                            tags_text = content.strip()
                            # 处理中文逗号和空格
                            tags = [tag.strip() for tag in tags_text.replace('，', ',').split(',') if tag.strip()]
                            return tags[:10]  # 限制最多10个标签
                    
                    return self._fallback_analysis(image_path)
                    
                except Exception as e:
                    error_str = str(e)
                    
                    # 检查是否是配额限制或速率限制错误
                    is_rate_limit = any(keyword in error_str.lower() for keyword in [
                        'quota', 'rate limit', 'too many requests', '429', 
                        '请求过于频繁', '配额', '限流'
                    ])
                    
                    if is_rate_limit and attempt < max_retries - 1:
                        # 速率限制，使用指数退避
                        retry_delay = base_delay * (2 ** attempt)
                        
                        # 尝试从错误信息中提取延迟时间
                        import re
                        delay_match = re.search(r'(\d+\.?\d*)\s*秒', error_str)
                        if not delay_match:
                            delay_match = re.search(r'(\d+\.?\d*)\s*seconds?', error_str, re.IGNORECASE)
                        
                        if delay_match:
                            extracted_delay = float(delay_match.group(1))
                            retry_delay = extracted_delay + 2  # 额外加2秒缓冲
                        
                        print(f"智谱AI API速率限制，等待 {retry_delay:.1f} 秒后重试 (尝试 {attempt + 1}/{max_retries})...")
                        time.sleep(retry_delay)
                        continue
                    elif attempt < max_retries - 1:
                        # 其他错误，也进行重试
                        retry_delay = base_delay * (2 ** attempt)
                        print(f"智谱AI API调用出错，等待 {retry_delay:.1f} 秒后重试 (尝试 {attempt + 1}/{max_retries})...")
                        print(f"错误: {e}")
                        time.sleep(retry_delay)
                        continue
                    else:
                        # 最后一次尝试失败，抛出异常让外层处理
                        raise
            
            return self._fallback_analysis(image_path)
            
        except ImportError:
            print("智谱AI SDK 未安装，请运行: pip install zhipuai")
            return self._fallback_analysis(image_path)
        except Exception as e:
            print(f"智谱AI分析失败: {e}")
            # 打印更详细的错误以便调试
            import traceback
            traceback.print_exc()
            return self._fallback_analysis(image_path)

    def _analyze_with_gemini(self, image_path: str) -> List[str]:
        """使用 Google Gemini (Stable SDK: google-generativeai) 分析图片，带重试和容错机制"""
        try:
            # 【改动1】使用更稳定的旧版导入方式
            import google.generativeai as genai
            import os
            import PIL.Image
            from google.api_core import exceptions as google_exceptions
            
            os.environ["HTTP_PROXY"] = "http://127.0.0.1:20171"
            os.environ["HTTPS_PROXY"] = "http://127.0.0.1:20171"
            # 获取配置
            api_key = self.gemini_api_key
            if not api_key:
                raise RuntimeError('GEMINI_API_KEY 未配置')
            
            # 【改动2】配置 API Key
            genai.configure(api_key=api_key)
            
            # 【改动3】使用 PIL 读取图片 (比手动转 Base64 更安全)
            img = PIL.Image.open(image_path)

            prompt = "请分析这张图片，生成5-10个中文标签，覆盖场景、主体、颜色或情绪等信息，只输出逗号分隔的标签，不要额外文字。"

            # 【改动4】旧版 SDK 的调用方式
            # 使用 gemini-2.0-flash 模型，因为它免费且快
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            # 【改动5】添加重试机制
            max_retries = 3
            base_delay = 1  # 基础延迟（秒）
            
            for attempt in range(max_retries):
                try:
                    response = model.generate_content([prompt, img])
                    
                    # 解析结果
                    if response.text:
                        text = response.text
                        # 处理中文逗号和空格
                        tags = [tag.strip() for tag in text.replace('，', ',').split(',') if tag.strip()]
                        return tags[:10]
                    
                    return self._fallback_analysis(image_path)
                    
                except google_exceptions.ResourceExhausted as e:
                    # 配额限制错误，需要等待后重试
                    retry_delay = base_delay * (2 ** attempt)  # 指数退避
                    
                    # 尝试从错误信息中提取建议的重试延迟
                    error_str = str(e)
                    import re
                    
                    # 尝试多种格式提取延迟时间
                    # 格式1: "retry in 51.339542764s" 或 "retry in 51 seconds"
                    delay_match = re.search(r'retry\s+in\s+(\d+\.?\d*)\s*s', error_str, re.IGNORECASE)
                    if not delay_match:
                        # 格式2: "seconds: 51" (从 retry_delay 块中)
                        delay_match = re.search(r'seconds:\s*(\d+\.?\d*)', error_str, re.IGNORECASE)
                    if not delay_match:
                        # 格式3: 直接查找数字+秒
                        delay_match = re.search(r'(\d+\.?\d*)\s*seconds?', error_str, re.IGNORECASE)
                    
                    if delay_match:
                        extracted_delay = float(delay_match.group(1))
                        # 使用提取的延迟时间，并额外加5秒缓冲以确保安全
                        retry_delay = extracted_delay + 5
                        print(f"从错误信息中提取到重试延迟: {extracted_delay:.1f} 秒，实际等待: {retry_delay:.1f} 秒")
                    
                    if attempt < max_retries - 1:
                        print(f"Gemini API配额限制，等待 {retry_delay:.1f} 秒后重试 (尝试 {attempt + 1}/{max_retries})...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        print(f"Gemini分析失败: 已达到最大重试次数 ({max_retries})，配额限制仍未解除")
                        print(f"错误详情: {e}")
                        return self._fallback_analysis(image_path)
                        
                except Exception as e:
                    # 其他类型的错误，如果是最后一次尝试，则回退
                    if attempt < max_retries - 1:
                        retry_delay = base_delay * (2 ** attempt)
                        print(f"Gemini API调用出错，等待 {retry_delay:.1f} 秒后重试 (尝试 {attempt + 1}/{max_retries})...")
                        print(f"错误: {e}")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise  # 重新抛出异常，让外层catch处理
            
            return self._fallback_analysis(image_path)

        except ImportError:
            print("Gemini SDK 未安装，请运行: pip install google-generativeai")
            return self._fallback_analysis(image_path)
        except Exception as e:
            print(f"Gemini分析失败: {e}")
            # 打印更详细的错误以便调试
            import traceback
            traceback.print_exc()
            return self._fallback_analysis(image_path)
    
    def _analyze_with_local_model(self, image_path: str) -> List[str]:
        """使用本地AI模型分析（如使用transformers库）"""
        try:
            from transformers import pipeline
            from PIL import Image
            
            # 使用预训练的图片分类模型
            classifier = pipeline("image-classification", 
                                model="microsoft/resnet-50")
            
            image = Image.open(image_path)
            results = classifier(image)
            
            # 转换为中文标签
            tags = []
            label_mapping = {
                'landscape': '风景',
                'nature': '自然',
                'person': '人物',
                'building': '建筑',
                'city': '城市',
                'water': '水',
                'mountain': '山脉',
                'beach': '海滩',
                'sunset': '日落',
                'sunrise': '日出',
                'flower': '花朵',
                'tree': '树木',
                'animal': '动物',
                'portrait': '肖像',
                'street': '街道',
                'sky': '天空',
                'cloud': '云朵',
                'ocean': '海洋',
                'forest': '森林',
                'garden': '花园'
            }
            
            for result in results[:5]:  # 取前5个结果
                label = result['label'].lower()
                chinese_tag = label_mapping.get(label, label)
                if chinese_tag not in tags:
                    tags.append(chinese_tag)
            
            return tags if tags else self._fallback_analysis(image_path)
            
        except ImportError:
            print("Transformers库未安装，请运行: pip install transformers torch")
            return self._fallback_analysis(image_path)
        except Exception as e:
            print(f"本地模型分析失败: {e}")
            return self._fallback_analysis(image_path)
    
    def _fallback_analysis(self, image_path: str) -> List[str]:
        """回退方案：基于文件名和OpenCV的简单分析"""
        import os
        import cv2
        import numpy as np
        
        filename = os.path.basename(image_path).lower()
        ai_tags = []
        
        # 基于文件名的简单分析
        if any(word in filename for word in ['sunset', 'sunrise', 'sun', 'sky']):
            ai_tags.extend(['日落', '天空', '风景'])
        elif any(word in filename for word in ['mountain', 'hill', 'peak']):
            ai_tags.extend(['山脉', '自然', '风景'])
        elif any(word in filename for word in ['sea', 'ocean', 'beach', 'water']):
            ai_tags.extend(['海洋', '海滩', '水'])
        elif any(word in filename for word in ['city', 'building', 'street']):
            ai_tags.extend(['城市', '建筑', '街道'])
        elif any(word in filename for word in ['flower', 'tree', 'plant']):
            ai_tags.extend(['植物', '花朵', '自然'])
        elif any(word in filename for word in ['person', 'people', 'face']):
            ai_tags.extend(['人物', '肖像'])
        else:
            ai_tags.extend(['图片', '照片'])
        
        # 使用OpenCV进行颜色和亮度分析
        try:
            img = cv2.imread(image_path)
            if img is not None:
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                
                # 检测主要颜色
                hue_mean = np.mean(hsv[:,:,0])
                if hue_mean < 30:
                    ai_tags.append('红色')
                elif 30 <= hue_mean < 60:
                    ai_tags.append('黄色')
                elif 60 <= hue_mean < 90:
                    ai_tags.append('绿色')
                elif 90 <= hue_mean < 120:
                    ai_tags.append('青色')
                elif 120 <= hue_mean < 150:
                    ai_tags.append('蓝色')
                else:
                    ai_tags.append('紫色')
                
                # 亮度分析
                brightness = np.mean(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
                if brightness > 200:
                    ai_tags.append('明亮')
                elif brightness < 50:
                    ai_tags.append('昏暗')
                else:
                    ai_tags.append('中等亮度')
        except Exception:
            pass  # OpenCV不可用，跳过
        
        return list(set(ai_tags))  # 去重


# 全局分析器实例
_analyzer = None

def get_analyzer() -> AIAnalyzer:
    """获取AI分析器单例"""
    global _analyzer
    if _analyzer is None:
        _analyzer = AIAnalyzer()
    return _analyzer

def split_tags_by_pause(tags: List[str]) -> List[str]:
    """将包含顿号的标签分割成多个独立标签"""
    result = []
    for tag in tags:
        tag = tag.strip()
        if not tag:
            continue
        # 如果包含顿号，按顿号分割
        if '、' in tag:
            sub_tags = [sub_tag.strip() for sub_tag in tag.split('、') if sub_tag.strip()]
            result.extend(sub_tags)
        else:
            result.append(tag)
    return result

def analyze_image_with_ai(image_path: str) -> List[str]:
    """
    分析图片并返回标签列表
    这是对外提供的统一接口
    返回的标签会自动按顿号分割
    """
    analyzer = get_analyzer()
    tags = analyzer.analyze(image_path)
    # 确保返回的标签已经按顿号分割
    return split_tags_by_pause(tags) if tags else []

