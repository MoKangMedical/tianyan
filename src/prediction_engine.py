"""
Prediction Engine — 预测引擎
市场趋势预测、人群行为预测、商业指标预测
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
import math
import random
import time


class PredictionType(Enum):
    """预测类型"""
    MARKET_TREND = "market_trend"
    CONSUMER_BEHAVIOR = "consumer_behavior"
    COMPETITIVE_LANDSCAPE = "competitive_landscape"
    REVENUE_FORECAST = "revenue_forecast"
    RISK_ASSESSMENT = "risk_assessment"


@dataclass
class PredictionRequest:
    """预测请求"""
    prediction_type: PredictionType
    time_horizon: int  # 天数
    parameters: Dict[str, Any]
    confidence_level: float = 0.95


@dataclass
class PredictionResult:
    """预测结果"""
    prediction_id: str
    prediction_type: str
    forecast: List[Dict]
    confidence_interval: Dict
    key_drivers: List[str]
    risks: List[str]
    recommendations: List[str]
    execution_time: float


class PredictionEngine:
    """预测引擎"""
    
    def __init__(self):
        self.historical_data: Dict[str, List] = {}
        self.models: Dict[str, Any] = {}
        self.predictions: List[PredictionResult] = []
    
    def predict(self, request: PredictionRequest) -> PredictionResult:
        """执行预测"""
        start_time = time.time()
        prediction_id = f"pred_{int(time.time())}"
        
        # 根据类型选择预测方法
        if request.prediction_type == PredictionType.MARKET_TREND:
            forecast = self._predict_market_trend(request)
        elif request.prediction_type == PredictionType.CONSUMER_BEHAVIOR:
            forecast = self._predict_consumer_behavior(request)
        elif request.prediction_type == PredictionType.REVENUE_FORECAST:
            forecast = self._predict_revenue(request)
        else:
            forecast = self._generic_predict(request)
        
        # 计算置信区间
        confidence = self._calculate_confidence(forecast, request.confidence_level)
        
        # 识别关键驱动因素
        drivers = self._identify_drivers(request)
        
        # 识别风险
        risks = self._identify_risks(request)
        
        # 生成建议
        recommendations = self._generate_recommendations(request, forecast)
        
        result = PredictionResult(
            prediction_id=prediction_id,
            prediction_type=request.prediction_type.value,
            forecast=forecast,
            confidence_interval=confidence,
            key_drivers=drivers,
            risks=risks,
            recommendations=recommendations,
            execution_time=time.time() - start_time
        )
        
        self.predictions.append(result)
        return result
    
    def _predict_market_trend(self, request: PredictionRequest) -> List[Dict]:
        """市场趋势预测"""
        days = request.time_horizon
        base_value = request.parameters.get("base_value", 100)
        growth_rate = request.parameters.get("growth_rate", 0.05)
        
        forecast = []
        for day in range(0, days, 7):  # 每周一个数据点
            value = base_value * (1 + growth_rate) ** (day / 30)
            noise = random.gauss(0, value * 0.02)
            forecast.append({
                "day": day,
                "date": f"Day {day}",
                "value": round(value + noise, 2),
                "trend": "up" if growth_rate > 0 else "down"
            })
        
        return forecast
    
    def _predict_consumer_behavior(self, request: PredictionRequest) -> List[Dict]:
        """消费者行为预测"""
        segments = request.parameters.get("segments", ["年轻白领", "中年家庭", "老年健康"])
        
        forecast = []
        for segment in segments:
            forecast.append({
                "segment": segment,
                "purchase_probability": round(random.uniform(0.3, 0.8), 2),
                "avg_order_value": round(random.uniform(100, 500), 2),
                "loyalty_score": round(random.uniform(0.5, 0.95), 2),
                "churn_risk": round(random.uniform(0.05, 0.3), 2)
            })
        
        return forecast
    
    def _predict_revenue(self, request: PredictionRequest) -> List[Dict]:
        """收入预测"""
        months = request.time_horizon // 30
        base_revenue = request.parameters.get("base_revenue", 100000)
        growth_rate = request.parameters.get("growth_rate", 0.1)
        
        forecast = []
        for month in range(1, months + 1):
            revenue = base_revenue * (1 + growth_rate / 12) ** month
            noise = random.gauss(0, revenue * 0.05)
            forecast.append({
                "month": month,
                "revenue": round(revenue + noise, 2),
                "growth": round(growth_rate * 100 / 12, 2)
            })
        
        return forecast
    
    def _generic_predict(self, request: PredictionRequest) -> List[Dict]:
        """通用预测"""
        return [{"day": i, "value": round(random.uniform(50, 150), 2)} 
                for i in range(0, request.time_horizon, 7)]
    
    def _calculate_confidence(self, forecast: List[Dict], level: float) -> Dict:
        """计算置信区间"""
        values = [f.get("value", 0) for f in forecast if "value" in f]
        if not values:
            return {"lower": 0, "upper": 0}
        
        mean = sum(values) / len(values)
        std = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
        
        z_score = 1.96 if level >= 0.95 else 1.645
        
        return {
            "lower": round(mean - z_score * std, 2),
            "upper": round(mean + z_score * std, 2),
            "mean": round(mean, 2)
        }
    
    def _identify_drivers(self, request: PredictionRequest) -> List[str]:
        """识别关键驱动因素"""
        drivers_map = {
            PredictionType.MARKET_TREND: ["市场规模", "增长率", "政策支持", "技术进步"],
            PredictionType.CONSUMER_BEHAVIOR: ["价格敏感度", "品牌忠诚度", "产品创新", "营销投入"],
            PredictionType.REVENUE_FORECAST: ["用户增长", "ARPU", "转化率", "留存率"],
            PredictionType.COMPETITIVE_LANDSCAPE: ["市场份额", "产品差异化", "渠道覆盖", "品牌影响力"],
            PredictionType.RISK_ASSESSMENT: ["市场波动", "政策变化", "竞争加剧", "技术替代"]
        }
        return drivers_map.get(request.prediction_type, ["市场因素", "竞争因素", "内部因素"])
    
    def _identify_risks(self, request: PredictionRequest) -> List[str]:
        """识别风险"""
        return ["市场波动风险", "政策变化风险", "竞争加剧风险", "技术替代风险"]
    
    def _generate_recommendations(self, request: PredictionRequest, forecast: List[Dict]) -> List[str]:
        """生成建议"""
        return [
            "持续监控市场变化",
            "加强产品差异化",
            "优化成本结构",
            "拓展新市场"
        ]
    
    def get_prediction_history(self) -> List[Dict]:
        """获取预测历史"""
        return [
            {
                "prediction_id": p.prediction_id,
                "type": p.prediction_type,
                "execution_time": p.execution_time
            }
            for p in self.predictions
        ]
