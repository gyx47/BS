# AI图片分析配置指南

本系统支持多种AI服务来分析图片内容并自动生成标签。系统会按优先级自动选择可用的AI服务。

## 支持的AI服务

### 1. OpenAI Vision API（推荐）

使用GPT-4 Vision模型进行图片分析，准确度最高。

#### 配置步骤：

1. **获取API密钥**
   - 访问 [OpenAI官网](https://platform.openai.com/)
   - 注册账号并创建API密钥

2. **安装依赖**
   ```bash
   pip install openai
   ```

3. **配置环境变量**
   在项目根目录的 `.env` 文件中添加：
   ```env
   AI_PROVIDER=openai
   AI_API_KEY=sk-your-openai-api-key-here
   ```

4. **使用**
   上传图片时，系统会自动调用OpenAI Vision API分析图片内容，生成中文标签。

#### 费用说明
- GPT-4 Vision按图片大小和token数量计费
- 建议设置API使用限额以避免意外费用

---

### 2. Google Cloud Vision API

使用Google的视觉识别服务，支持多种语言。

#### 配置步骤：

1. **创建Google Cloud项目**
   - 访问 [Google Cloud Console](https://console.cloud.google.com/)
   - 创建新项目并启用Vision API

2. **获取服务账号密钥**
   - 创建服务账号并下载JSON密钥文件
   - 设置环境变量：`GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json`

3. **安装依赖**
   ```bash
   pip install google-cloud-vision
   ```

4. **配置环境变量**
   ```env
   AI_PROVIDER=google
   AI_API_KEY=your-google-api-key  # 可选，如果使用服务账号则不需要
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
   ```

---

### 3. 本地AI模型（Transformers）

使用Hugging Face的预训练模型，无需API调用，完全免费。

#### 配置步骤：

1. **安装依赖**
   ```bash
   pip install transformers torch torchvision
   ```

2. **配置环境变量**
   ```env
   AI_PROVIDER=local
   ```

3. **首次使用**
   - 首次运行时会自动下载模型（约500MB）
   - 后续使用无需网络连接

#### 注意事项
- 需要较大的内存（建议8GB+）
- 首次下载模型需要较长时间
- 分析速度较API服务慢

---

### 4. 回退方案（默认）

如果未配置任何AI服务，系统会使用基于文件名和OpenCV的简单分析。

#### 特点：
- ✅ 无需配置，开箱即用
- ✅ 完全免费
- ✅ 无需网络连接
- ❌ 准确度较低
- ❌ 只能识别文件名关键词和颜色特征

#### 配置
```env
AI_PROVIDER=fallback
# 或直接不设置AI_PROVIDER
```

---

## 环境变量配置示例

完整的 `.env` 文件示例：

```env
# 数据库配置
DB_USER=photo
DB_PASSWORD=photo
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=photo_management

# AI服务配置（选择一种）
# 选项1: OpenAI
AI_PROVIDER=openai
AI_API_KEY=sk-your-key-here

# 选项2: Google Vision
# AI_PROVIDER=google
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json

# 选项3: 本地模型
# AI_PROVIDER=local

# 选项4: 回退方案（默认）
# AI_PROVIDER=fallback
```

---

## 使用建议

### 开发环境
- 使用**回退方案**或**本地模型**，避免产生API费用

### 生产环境
- 小规模使用：**本地模型**（免费，但需要服务器资源）
- 大规模使用：**OpenAI Vision**（准确度高，按量付费）
- 企业级：**Google Vision**（稳定可靠，有免费额度）

---

## 测试AI分析功能

1. **配置AI服务**（选择上述任一方案）

2. **上传测试图片**
   ```bash
   # 启动后端
   python server.py
   
   # 在前端上传一张包含明显内容的图片（如风景、人物等）
   ```

3. **查看生成的标签**
   - 上传成功后，在图片详情页查看自动生成的标签
   - 标签类型为 `auto`，表示由AI自动生成

---

## 故障排查

### OpenAI API错误
- 检查API密钥是否正确
- 确认账户有足够余额
- 检查网络连接

### Google Vision错误
- 确认已启用Vision API
- 检查服务账号密钥路径
- 确认有足够的API配额

### 本地模型错误
- 确认已安装torch和transformers
- 检查系统内存是否充足
- 首次使用需要下载模型，确保网络畅通

### 回退方案
- 如果所有AI服务都失败，系统会自动使用回退方案
- 回退方案基于文件名和颜色分析，准确度较低

---

### 5. Google Gemini (gemini-1.5 / 2.x Flash)

使用 Google 的 Gemini 多模态模型，支持免费配额（需 Google 账号），可直接解析图像并输出中文标签。

#### 配置步骤：

1. **启用 Gemini API**
   - 访问 [Google AI Studio](https://aistudio.google.com/)
   - 创建 API Key（免费额度可用）

2. **安装依赖**
   ```bash
   pip install google-genai
   ```

3. **配置环境变量**
   ```env
   AI_PROVIDER=gemini
   GEMINI_API_KEY=你的Gemini密钥
   GEMINI_MODEL=gemini-1.5-flash   # 可选，默认1.5 flash，可改成 gemini-2.0-flash 等
   ```

4. **特点**
   - ✅ 官方免费额度
   - ✅ 原生多模态支持，能直接解析图片
   - ⚠️ 需科学上网访问部分区域
   - ⚠️ 首次调用需要等待模型加载

---

## 自定义标签映射

如果需要自定义英文标签到中文的映射，可以编辑 `utils/ai_analyzer.py` 中的 `label_mapping` 字典。

---

## 性能优化建议

1. **批量处理**：对于大量图片，考虑实现批量分析接口
2. **缓存结果**：相同图片的AI分析结果可以缓存
3. **异步处理**：将AI分析改为异步任务，避免阻塞上传流程
4. **图片压缩**：上传前压缩图片可以降低API调用成本

---

## 更多信息

- [OpenAI Vision API文档](https://platform.openai.com/docs/guides/vision)
- [Google Cloud Vision API文档](https://cloud.google.com/vision/docs)
- [Hugging Face Transformers文档](https://huggingface.co/docs/transformers)

