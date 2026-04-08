"""
实时数据集成 — 从外部数据源获取实时数据

适配器：
- StockFeedAdapter：A股实时数据（akshare）
- NewsFeedAdapter：行业新闻RSS
- PolicyFeedAdapter：政策法规更新
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class FeedItem:
    """数据条目。"""
    title: str
    source: str
    content: str
    url: str = ""
    timestamp: str = ""
    category: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "source": self.source,
            "content": self.content,
            "url": self.url,
            "timestamp": self.timestamp,
            "category": self.category,
            "metadata": self.metadata,
        }


class BaseFeedAdapter(ABC):
    """数据源基类。"""

    def __init__(self, name: str):
        self.name = name
        self._last_fetch: float = 0
        self._cache: list[FeedItem] = []
        self._cache_ttl: int = 300  # 5分钟

    @abstractmethod
    def _do_fetch(self, **kwargs) -> list[FeedItem]:
        """实际抓取逻辑。"""
        ...

    def fetch_latest(self, force: bool = False, **kwargs) -> list[FeedItem]:
        """获取最新数据（带缓存）。"""
        now = time.time()
        if not force and (now - self._last_fetch) < self._cache_ttl and self._cache:
            return self._cache

        try:
            self._cache = self._do_fetch(**kwargs)
            self._last_fetch = now
        except Exception as e:
            # 降级返回缓存
            if not self._cache:
                self._cache = [FeedItem(
                    title=f"{self.name}数据获取失败",
                    source=self.name,
                    content=f"错误: {str(e)}",
                    timestamp=datetime.now().isoformat(),
                )]
        return self._cache


class StockFeedAdapter(BaseFeedAdapter):
    """
    A股股票行情适配器。

    关注的健康/减重相关上市公司：
    - 诺和诺德/礼来（GLP-1原研）
    - 信达生物/恒瑞医药/华东医药（GLP-1仿制药）
    - 汤臣倍健（保健品）
    - 京东健康/阿里健康（健康消费渠道）
    """

    TRACKED_STOCKS = {
        "600276": {"name": "恒瑞医药", "relevance": "GLP-1管线"},
        "000963": {"name": "华东医药", "relevance": "GLP-1管线"},
        "300146": {"name": "汤臣倍健", "relevance": "保健品龙头"},
        "6618": {"name": "京东健康", "relevance": "健康消费渠道"},
        "241": {"name": "阿里健康", "relevance": "健康消费渠道"},
    }

    def __init__(self):
        super().__init__("stock_feed")

    def _do_fetch(self, **kwargs) -> list[FeedItem]:
        """通过akshare获取股票数据。"""
        items = []
        try:
            import akshare as ak
            for code, info in self.TRACKED_STOCKS.items():
                try:
                    # 实时行情
                    df = ak.stock_zh_a_spot_em()
                    row = df[df["代码"] == code]
                    if not row.empty:
                        r = row.iloc[0]
                        items.append(FeedItem(
                            title=f"{info['name']}({code})",
                            source="akshare",
                            content=f"最新价: {r.get('最新价', '?')} | 涨跌幅: {r.get('涨跌幅', '?')}% | 成交额: {r.get('成交额', '?')}",
                            timestamp=datetime.now().isoformat(),
                            category="stock",
                            metadata={
                                "code": code,
                                "price": float(r.get("最新价", 0)),
                                "change_pct": float(r.get("涨跌幅", 0)),
                                "volume": float(r.get("成交额", 0)),
                                "relevance": info["relevance"],
                            },
                        ))
                except Exception:
                    continue
        except ImportError:
            # akshare未安装，返回静态数据
            for code, info in self.TRACKED_STOCKS.items():
                items.append(FeedItem(
                    title=f"{info['name']}({code})",
                    source="static",
                    content=f"[需要安装akshare获取实时数据] 相关性: {info['relevance']}",
                    timestamp=datetime.now().isoformat(),
                    category="stock",
                    metadata={"code": code, "relevance": info["relevance"]},
                ))
        return items

    def get_tracked_list(self) -> dict:
        """返回追踪股票清单。"""
        return self.TRACKED_STOCKS


class NewsFeedAdapter(BaseFeedAdapter):
    """
    行业新闻适配器。

    从公开RSS源获取健康/医药/消费行业新闻。
    """

    # 关注的RSS源
    RSS_SOURCES = {
        "健康界": "https://www.cacaw.cn/rss",
        "动脉网": "https://vcbeat.top/rss",
        "丁香园": "https://www.dxy.cn/rss",
    }

    # 关键词过滤
    KEYWORDS = [
        "GLP-1", "司美格鲁肽", "替尔泊肽", "减重", "减肥",
        "消费医疗", "远程医疗", "互联网医院",
        "保健品", "营养补充", "益生菌",
        "AI医疗", "数字健康", "医疗AI",
    ]

    def __init__(self):
        super().__init__("news_feed")

    def _do_fetch(self, keywords: list[str] = None, **kwargs) -> list[FeedItem]:
        """从RSS获取新闻。"""
        items = []
        kw = keywords or self.KEYWORDS

        try:
            import feedparser
            for source_name, url in self.RSS_SOURCES.items():
                try:
                    feed = feedparser.parse(url)
                    for entry in feed.entries[:20]:
                        title = entry.get("title", "")
                        summary = entry.get("summary", "")
                        # 关键词过滤
                        if any(k in title + summary for k in kw):
                            items.append(FeedItem(
                                title=title,
                                source=source_name,
                                content=summary[:500],
                                url=entry.get("link", ""),
                                timestamp=entry.get("published", ""),
                                category="news",
                            ))
                except Exception:
                    continue
        except ImportError:
            # feedparser未安装，返回模拟数据
            items = [
                FeedItem(
                    title="[需要安装feedparser] 行业新闻获取器",
                    source="system",
                    content="pip install feedparser 后可获取实时行业新闻",
                    timestamp=datetime.now().isoformat(),
                    category="news",
                )
            ]
        return items


class PolicyFeedAdapter(BaseFeedAdapter):
    """
    政策法规适配器。

    从政府公开渠道获取最新政策信息。
    """

    POLICY_SOURCES = {
        "国家卫健委": "http://www.nhc.gov.cn/",
        "国家医保局": "http://www.nhsa.gov.cn/",
        "国家药监局": "https://www.nmpa.gov.cn/",
        "国务院": "https://www.gov.cn/",
    }

    POLICY_KEYWORDS = [
        "体重管理", "肥胖", "减重", "GLP-1", "司美格鲁肽",
        "互联网诊疗", "远程医疗", "处方药",
        "保健食品", "营养", "食品安全",
        "医保", "集采", "药品审批",
    ]

    def __init__(self):
        super().__init__("policy_feed")

    def _do_fetch(self, **kwargs) -> list[FeedItem]:
        """获取政策数据。"""
        # 政策数据通常需要爬虫或手动录入
        # 这里提供预置的重要政策
        now = datetime.now().isoformat()
        return [
            FeedItem(
                title="体重管理年活动实施方案",
                source="国家卫健委等16部门",
                content="2024-2026年开展体重管理年活动，建设支持性环境，建立体重管理门诊体系",
                url="http://www.nhc.gov.cn/",
                timestamp="2024-06-26",
                category="policy",
                metadata={"importance": "high", "impact": "weight_management"},
            ),
            FeedItem(
                title="司美格鲁肽专利2026年到期",
                source="公开信息",
                content="诺和诺德司美格鲁肽中国专利2026年到期，多家企业布局仿制药",
                timestamp="2024",
                category="policy",
                metadata={"importance": "high", "impact": "glp1_market"},
            ),
            FeedItem(
                title="互联网诊疗管理办法",
                source="国家卫健委",
                content="规范互联网诊疗活动，明确互联网医院资质要求和处方药销售规范",
                url="http://www.nhc.gov.cn/",
                timestamp="2018-09-14",
                category="policy",
                metadata={"importance": "high", "impact": "telehealth"},
            ),
            FeedItem(
                title="保健食品注册与备案管理办法",
                source="国家市场监督管理总局",
                content="规范保健食品注册和备案管理，明确功能声称和标签要求",
                timestamp="2016-07-01",
                category="policy",
                metadata={"importance": "medium", "impact": "health_food"},
            ),
        ]


class RealtimeFeedManager:
    """
    实时数据源管理器。

    统一管理所有数据源适配器。
    """

    def __init__(self):
        self.stock = StockFeedAdapter()
        self.news = NewsFeedAdapter()
        self.policy = PolicyFeedAdapter()

    def get_dashboard_data(self) -> dict[str, Any]:
        """获取Dashboard所需的所有实时数据。"""
        return {
            "stocks": [item.to_dict() for item in self.stock.fetch_latest()],
            "news": [item.to_dict() for item in self.news.fetch_latest()],
            "policy": [item.to_dict() for item in self.policy.fetch_latest()],
            "updated_at": datetime.now().isoformat(),
        }

    def get_stock_trends(self) -> list[dict]:
        """获取股票趋势数据。"""
        return [item.to_dict() for item in self.stock.fetch_latest()]

    def get_news_feed(self, limit: int = 20) -> list[dict]:
        """获取新闻流。"""
        items = self.news.fetch_latest()
        return [item.to_dict() for item in items[:limit]]
