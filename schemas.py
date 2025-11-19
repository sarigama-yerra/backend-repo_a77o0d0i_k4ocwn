"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- BlogPost -> "blogpost" collection
- ContactMessage -> "contactmessage" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password_hash: str = Field(..., description="Password hash with salt")
    password_salt: str = Field(..., description="Per-user password salt")
    avatar_url: Optional[str] = Field(None, description="Optional avatar URL")
    plan: str = Field("free", description="Subscription plan: free, pro, business")
    is_verified: bool = Field(False, description="Whether email is verified")

class BlogPost(BaseModel):
    """
    Blog posts collection schema
    Collection name: "blogpost"
    """
    title: str = Field(..., description="Post title")
    slug: str = Field(..., description="URL slug")
    excerpt: str = Field(..., description="Short summary")
    content: str = Field(..., description="Markdown content")
    tags: List[str] = Field(default_factory=list, description="Tags")
    author: str = Field("Team", description="Author name")
    cover_image: Optional[str] = Field(None, description="Cover image URL")
    published: bool = Field(True, description="Published flag")

class ContactMessage(BaseModel):
    """
    Contact messages collection schema
    Collection name: "contactmessage"
    """
    name: str = Field(..., description="Sender name")
    email: EmailStr = Field(..., description="Sender email")
    company: Optional[str] = Field(None, description="Company (optional)")
    message: str = Field(..., description="Message body")
    topic: Optional[str] = Field("General", description="Topic category")
