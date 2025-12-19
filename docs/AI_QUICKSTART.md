# AI图片分析快速开始

## 最简单的配置（5分钟）

### 方案1：使用回退方案（无需配置）

**什么都不用做！** 系统默认使用基于文件名和颜色的简单分析，开箱即用。

- ✅ 无需API密钥
- ✅ 无需额外依赖
- ✅ 完全免费
- ⚠️ 准确度较低

---

### 方案2：使用OpenAI Vision（推荐，准确度最高）

1. **安装依赖**
   ```bash
   pip install openai
   ```

2. **获取API密钥**
   - 访问 https://platform.openai.com/
   - 注册/登录账号
   - 创建API密钥

3. **配置环境变量**
   
   在项目根目录创建或编辑 `.env` 文件：
   ```env
   AI_PROVIDER=openai
   AI_API_KEY=sk-your-api-key-here
   ```

4. **完成！**
   
   现在上传图片时，系统会自动使用OpenAI分析图片内容。

---

### 方案3：使用本地AI模型（免费，无需API）

1. **安装依赖**
   ```bash
   pip install transformers torch torchvision
   ```

2. **配置环境变量**
   ```env
   AI_PROVIDER=local
   ```

3. **首次使用**
   - 首次运行时会自动下载模型（约500MB，需要几分钟）
   - 后续使用无需网络

- ✅ 或直接使用 Gemini（含免费额度）

#### 方案4：使用 Google Gemini（免费额度）

1. **安装依赖**
   ```bash
   pip install google-genai
   ```

2. **获取 Gemini API Key**
   - 访问 https://aistudio.google.com/
   - 创建 API 密钥，复制保存

3. **配置环境变量**
   ```env
   AI_PROVIDER=gemini
   GEMINI_API_KEY=你的密钥
   GEMINI_MODEL=gemini-1.5-flash   # 可选，默认1.5 flash，可以换成 gemini-2.0-flash 等
   ```

4. **完成！**
   - 上传图片即可由 Gemini 自动打标签
   - 若调用失败，系统会自动回退到其他方案

---

## 测试

1. 启动后端服务
   ```bash
   python server.py
   ```

2. 在前端上传一张图片（建议选择有明显内容的图片，如风景、人物等）

3. 查看生成的标签
   - 上传成功后，在图片详情页查看自动生成的标签
   - 标签类型为 `auto` 表示由AI自动生成

---

## 常见问题

**Q: 如何知道当前使用的是哪个AI服务？**

A: 查看后端控制台输出。如果看到 "OpenAI分析失败" 或 "Google Vision分析失败" 等消息，说明正在尝试使用该服务但失败了，会自动回退到下一个方案。

**Q: OpenAI API调用失败怎么办？**

A: 
- 检查API密钥是否正确
- 确认账户有足够余额
- 检查网络连接
- 系统会自动回退到下一个可用方案

**Q: 本地模型太慢了怎么办？**

A: 可以切换到OpenAI API（需要付费）或使用回退方案（免费但准确度低）。

**Q: 如何切换AI服务？**

A: 修改 `.env` 文件中的 `AI_PROVIDER` 值，然后重启后端服务。

---

## 更多信息

详细配置说明请参考：[AI_CONFIGURATION.md](./AI_CONFIGURATION.md)

