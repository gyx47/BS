#!/usr/bin/env python3
"""
MCP (Model Context Protocol) 服务器
为图片管理网站提供大模型对话接口
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.server.lowlevel.server import NotificationOptions
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    Resource,
    ListResourcesRequest,
    ListResourcesResult,
    ReadResourceRequest,
    ReadResourceResult,
    ServerCapabilities,
)
import requests
import base64
from PIL import Image
import io

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建MCP服务器
server = Server("photo-management-mcp")

@dataclass
class PhotoInfo:
    id: int
    filename: str
    original_filename: str
    width: int
    height: int
    file_size: int
    taken_at: Optional[str]
    location: Optional[str]
    tags: List[str]
    thumbnail_url: str

class PhotoManagementMCP:
    def __init__(self, api_base_url: str = "http://localhost:5000", jwt_token: str = None):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.jwt_token = jwt_token or os.getenv('MCP_JWT_TOKEN')
        
        # 如果没有提供 token，尝试登录获取
        if not self.jwt_token:
            self._try_login()
        
    def _try_login(self):
        """尝试使用默认凭据登录获取 JWT token，如果失败则尝试注册"""
        try:
            # 尝试使用环境变量中的凭据，或使用默认值（用户名至少6个字符）
            username = os.getenv('MCP_USERNAME', '123456')
            password = os.getenv('MCP_PASSWORD', '123456')
            email = os.getenv('MCP_EMAIL', 'mcpadmin@example.com')
            
            logger.info(f"🔐 MCP 登录尝试 - API地址: {self.api_base_url}")
            logger.info(f"📝 使用凭据 - 用户名: {username}, 邮箱: {email}, 密码长度: {len(password)}")
            
            login_url = f"{self.api_base_url}/api/login"
            logger.info(f"🌐 登录请求URL: {login_url}")
            
            login_data = {
                "username": username,
                "password": password
            }
            logger.info(f"📤 登录请求数据: {login_data}")
            
            response = self.session.post(login_url, json=login_data)
            logger.info(f"📥 登录响应状态码: {response.status_code}")
            logger.info(f"📥 登录响应内容: {response.text[:500]}")
            
            if response.status_code == 200:
                data = response.json()
                self.jwt_token = data.get('access_token')
                logger.info("✅ MCP 登录成功，已获取 JWT token")
            elif response.status_code == 401:
                # 登录失败，尝试注册默认用户
                logger.info(f"⚠️ 用户 {username} 登录失败(401)，尝试注册...")
                register_url = f"{self.api_base_url}/api/register"
                logger.info(f"🌐 注册请求URL: {register_url}")
                
                register_data = {
                    "username": username,
                    "password": password,
                    "email": email
                }
                logger.info(f"📤 注册请求数据: {register_data}")
                logger.info(f"📊 用户名长度: {len(username)}, 密码长度: {len(password)}, 邮箱格式: {'@' in email}")
                
                register_response = self.session.post(register_url, json=register_data)
                logger.info(f"📥 注册响应状态码: {register_response.status_code}")
                logger.info(f"📥 注册响应头: {dict(register_response.headers)}")
                
                try:
                    register_response_json = register_response.json()
                    logger.info(f"📥 注册响应JSON: {register_response_json}")
                except:
                    logger.info(f"📥 注册响应文本: {register_response.text}")
                
                if register_response.status_code == 201:
                    logger.info(f"✅ 成功注册用户 {username}，重新尝试登录...")
                    # 注册成功后重新登录
                    login_response = self.session.post(login_url, json=login_data)
                    logger.info(f"📥 重新登录响应状态码: {login_response.status_code}")
                    logger.info(f"📥 重新登录响应内容: {login_response.text[:500]}")
                    
                    if login_response.status_code == 200:
                        data = login_response.json()
                        self.jwt_token = data.get('access_token')
                        logger.info("✅ MCP 登录成功，已获取 JWT token")
                    else:
                        logger.error(f"❌ 注册后登录失败: {login_response.status_code} - {login_response.text}")
                elif register_response.status_code == 400:
                    # 用户可能已存在但密码错误，或其他注册错误
                    try:
                        error_msg = register_response.json().get('error', '')
                        logger.error(f"❌ 注册失败(400): {error_msg}")
                        if '已存在' in error_msg:
                            logger.warning(f"⚠️ 用户 {username} 已存在，但密码不正确。请检查 MCP_PASSWORD 环境变量")
                        elif '至少6个字符' in error_msg:
                            logger.error(f"❌ 用户名或密码长度不符合要求: {error_msg}")
                        elif '邮箱格式' in error_msg:
                            logger.error(f"❌ 邮箱格式不正确: {error_msg}")
                    except:
                        logger.error(f"❌ 注册失败(400)，无法解析错误信息: {register_response.text}")
                else:
                    logger.error(f"❌ 注册失败: 状态码={register_response.status_code}, 响应={register_response.text[:500]}")
            else:
                logger.error(f"❌ MCP 登录失败: 状态码={response.status_code}, 响应={response.text[:500]}")
        except requests.RequestException as e:
            logger.error(f"❌ MCP 网络请求异常: {type(e).__name__}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"❌ 响应状态码: {e.response.status_code}")
                logger.error(f"❌ 响应内容: {e.response.text[:500]}")
        except Exception as e:
            logger.error(f"❌ MCP 自动登录失败: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"❌ 异常堆栈: {traceback.format_exc()}")
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送API请求"""
        url = f"{self.api_base_url}{endpoint}"
        
        # 添加 JWT 认证头
        headers = kwargs.get('headers', {})
        if self.jwt_token:
            headers['Authorization'] = f'Bearer {self.jwt_token}'
        kwargs['headers'] = headers
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"响应内容: {e.response.text}")
            return {"error": str(e)}
    
    def search_photos(self, query: str, tags: List[str] = None, limit: int = 10) -> List[PhotoInfo]:
        """搜索照片"""
        params = {
            "per_page": limit
        }
        
        # 如果提供了标签，优先使用标签筛选（更精确）
        if tags and len(tags) > 0:
            params["tag"] = tags[0]  # 后端只支持单个标签筛选
            logger.info(f"使用标签筛选: {tags[0]}")
        elif query:
            # 如果没有标签，先尝试作为标签搜索
            # 后端tag参数支持精确匹配标签名
            params["tag"] = query
            logger.info(f"使用标签搜索: {query}")
            
        logger.info(f"API 请求参数: {params}")
        response = self._make_request("GET", "/api/photos", params=params)
        
        if "error" in response:
            logger.error(f"API 请求返回错误: {response.get('error')}")
            return []
        
        # 检查响应结构
        if "photos" not in response:
            logger.warning(f"API 响应中没有 'photos' 字段，响应内容: {response}")
            return []
            
        photos = []
        photo_list = response.get("photos", [])
        logger.info(f"API 返回 {len(photo_list)} 张照片")
        
        # 如果标签搜索没有结果，且提供了query，尝试文件名搜索
        if len(photo_list) == 0 and query and not tags:
            logger.info(f"标签搜索无结果，尝试文件名搜索: {query}")
            params = {
                "per_page": limit,
                "search": query
            }
            response = self._make_request("GET", "/api/photos", params=params)
            if "error" not in response and "photos" in response:
                photo_list = response.get("photos", [])
                logger.info(f"文件名搜索返回 {len(photo_list)} 张照片")
        
        for photo_data in photo_list:
            photos.append(PhotoInfo(
                id=photo_data["id"],
                filename=photo_data["filename"],
                original_filename=photo_data["original_filename"],
                width=photo_data["width"],
                height=photo_data["height"],
                file_size=photo_data["file_size"],
                taken_at=photo_data.get("taken_at"),
                location=photo_data.get("location"),
                tags=photo_data.get("tags", []),
                thumbnail_url=f"{self.api_base_url}/api/thumbnail/{photo_data['id']}"
            ))
        
        return photos
    
    def get_photo_details(self, photo_id: int) -> Optional[PhotoInfo]:
        """获取照片详情"""
        response = self._make_request("GET", f"/api/photo/{photo_id}")
        
        if "error" in response:
            return None
            
        return PhotoInfo(
            id=response["id"],
            filename=response["filename"],
            original_filename=response["original_filename"],
            width=response["width"],
            height=response["height"],
            file_size=response["file_size"],
            taken_at=response.get("taken_at"),
            location=response.get("location"),
            tags=response.get("tags", []),
            thumbnail_url=f"{self.api_base_url}/api/thumbnail/{response['id']}"
        )
    
    def get_photo_image(self, photo_id: int) -> Optional[bytes]:
        """获取照片图片数据"""
        try:
            headers = {}
            if self.jwt_token:
                headers['Authorization'] = f'Bearer {self.jwt_token}'
            response = self.session.get(
                f"{self.api_base_url}/api/photo/{photo_id}",
                headers=headers
            )
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            logger.error(f"获取图片失败: {e}")
            return None
    
    def analyze_image_with_ai(self, photo_id: int) -> Dict[str, Any]:
        """使用AI分析图片内容"""
        # 这里可以集成真实的AI服务，如OpenAI Vision API、Google Vision API等
        # 目前返回模拟数据
        return {
            "objects": ["人物", "建筑", "天空"],
            "scene": "城市风景",
            "colors": ["蓝色", "白色", "灰色"],
            "mood": "平静",
            "tags": ["城市", "建筑", "天空", "现代"]
        }

# 创建MCP实例
# 创建MCP实例，优先使用环境变量 MCP_API_BASE_URL（方便在容器中通过服务名访问后端）
photo_mcp = PhotoManagementMCP(api_base_url=os.getenv('MCP_API_BASE_URL', 'http://backend:5000'))

@server.list_tools()
async def list_tools() -> List[Tool]:
    """列出可用的工具"""
    return [
        Tool(
            name="search_photos",
            description="搜索照片，支持关键词和标签筛选",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "标签筛选"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量限制",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_photo_details",
            description="获取特定照片的详细信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "photo_id": {
                        "type": "integer",
                        "description": "照片ID"
                    }
                },
                "required": ["photo_id"]
            }
        ),
        Tool(
            name="analyze_photo",
            description="使用AI分析照片内容，识别对象、场景、颜色等",
            inputSchema={
                "type": "object",
                "properties": {
                    "photo_id": {
                        "type": "integer",
                        "description": "照片ID"
                    }
                },
                "required": ["photo_id"]
            }
        ),
        Tool(
            name="get_photo_image",
            description="获取照片的图片数据（用于显示）",
            inputSchema={
                "type": "object",
                "properties": {
                    "photo_id": {
                        "type": "integer",
                        "description": "照片ID"
                    }
                },
                "required": ["photo_id"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """调用工具"""
    try:
        if name == "search_photos":
            query = arguments.get("query", "")
            tags = arguments.get("tags", [])
            limit = arguments.get("limit", 10)
            
            photos = photo_mcp.search_photos(query, tags, limit)
            
            if not photos:
                return [TextContent(type="text", text="没有找到匹配的照片")]
            
            result = f"找到 {len(photos)} 张照片：\n\n"
            for photo in photos:
                result += f"📷 **{photo.original_filename}**\n"
                result += f"   - 尺寸: {photo.width} × {photo.height}\n"
                result += f"   - 大小: {photo.file_size / 1024:.1f} KB\n"
                if photo.taken_at:
                    result += f"   - 拍摄时间: {photo.taken_at}\n"
                if photo.location:
                    result += f"   - 地点: {photo.location}\n"
                if photo.tags:
                    result += f"   - 标签: {', '.join(photo.tags)}\n"
                result += f"   - 缩略图: {photo.thumbnail_url}\n\n"
            
            return [TextContent(type="text", text=result)]
        
        elif name == "get_photo_details":
            photo_id = arguments.get("photo_id")
            photo = photo_mcp.get_photo_details(photo_id)
            
            if not photo:
                return [TextContent(type="text", text=f"照片 ID {photo_id} 不存在")]
            
            result = f"📷 **{photo.original_filename}**\n\n"
            result += f"**基本信息:**\n"
            result += f"- 文件ID: {photo.id}\n"
            result += f"- 尺寸: {photo.width} × {photo.height}\n"
            result += f"- 文件大小: {photo.file_size / 1024:.1f} KB\n"
            
            if photo.taken_at:
                result += f"- 拍摄时间: {photo.taken_at}\n"
            if photo.location:
                result += f"- 拍摄地点: {photo.location}\n"
            
            if photo.tags:
                result += f"\n**标签:** {', '.join(photo.tags)}\n"
            
            result += f"\n**缩略图:** {photo.thumbnail_url}\n"
            
            return [TextContent(type="text", text=result)]
        
        elif name == "analyze_photo":
            photo_id = arguments.get("photo_id")
            analysis = photo_mcp.analyze_image_with_ai(photo_id)
            
            result = f"🔍 **照片分析结果 (ID: {photo_id})**\n\n"
            result += f"**识别对象:** {', '.join(analysis['objects'])}\n"
            result += f"**场景类型:** {analysis['scene']}\n"
            result += f"**主要颜色:** {', '.join(analysis['colors'])}\n"
            result += f"**情绪氛围:** {analysis['mood']}\n"
            result += f"**建议标签:** {', '.join(analysis['tags'])}\n"
            
            return [TextContent(type="text", text=result)]
        
        elif name == "get_photo_image":
            photo_id = arguments.get("photo_id")
            image_data = photo_mcp.get_photo_image(photo_id)
            
            if not image_data:
                return [TextContent(type="text", text=f"无法获取照片 ID {photo_id} 的图片数据")]
            
            # 将图片转换为base64编码
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            return [TextContent(
                type="text", 
                text=f"图片数据已获取 (ID: {photo_id})，大小: {len(image_data)} 字节"
            )]
        
        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]
    
    except Exception as e:
        logger.error(f"工具调用失败: {e}")
        return [TextContent(type="text", text=f"工具调用失败: {str(e)}")]

@server.list_resources()
async def list_resources() -> List[Resource]:
    """列出可用资源"""
    return [
        Resource(
            uri="photo-management://photos",
            name="照片列表",
            description="获取所有照片的列表",
            mimeType="application/json"
        ),
        Resource(
            uri="photo-management://tags",
            name="标签列表", 
            description="获取所有可用的标签",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def read_resource(uri: str) -> str:
    """读取资源内容"""
    if uri == "photo-management://photos":
        photos = photo_mcp.search_photos("", limit=100)
        return json.dumps([{
            "id": photo.id,
            "filename": photo.filename,
            "original_filename": photo.original_filename,
            "width": photo.width,
            "height": photo.height,
            "file_size": photo.file_size,
            "taken_at": photo.taken_at,
            "location": photo.location,
            "tags": photo.tags
        } for photo in photos], ensure_ascii=False, indent=2)
    
    elif uri == "photo-management://tags":
        # 这里应该从API获取标签列表
        return json.dumps(["风景", "人物", "建筑", "自然", "城市", "旅行"], ensure_ascii=False, indent=2)
    
    else:
        raise ValueError(f"未知资源: {uri}")

async def main():
    """主函数"""
    async with stdio_server() as (read_stream, write_stream):
        # 创建 NotificationOptions 对象并传递给 get_capabilities
        notification_options = NotificationOptions(resources_changed=False)
        
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="photo-management-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=notification_options,
                    experimental_capabilities=None
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
