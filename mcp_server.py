#!/usr/bin/env python3
"""
MCP (Model Context Protocol) 服务器
为图片管理网站提供大模型对话接口
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
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
    def __init__(self, api_base_url: str = "http://localhost:5000"):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送API请求"""
        url = f"{self.api_base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API请求失败: {e}")
            return {"error": str(e)}
    
    def search_photos(self, query: str, tags: List[str] = None, limit: int = 10) -> List[PhotoInfo]:
        """搜索照片"""
        params = {
            "search": query,
            "per_page": limit
        }
        if tags:
            params["tag"] = ",".join(tags)
            
        response = self._make_request("GET", "/api/photos", params=params)
        
        if "error" in response:
            return []
            
        photos = []
        for photo_data in response.get("photos", []):
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
            response = self.session.get(f"{self.api_base_url}/api/photo/{photo_id}")
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
photo_mcp = PhotoManagementMCP()

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
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="photo-management-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
