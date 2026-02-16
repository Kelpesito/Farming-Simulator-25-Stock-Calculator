from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# =================================================================================================
# Catalog
# =================================================================================================

@dataclass(frozen=True)
class CatalogProduct:
    id: str
    name_es: str
    name_en: str
    icon: str
    default_max_price_per_1000: float

    @staticmethod
    def from_dict(d: dict[str, Any]) -> CatalogProduct:
        return CatalogProduct(
            id=str(d["id"]),
            name_es=str(d.get("name_es", "")),
            name_en=str(d.get("name_en", "")),
            icon=str(d.get("icon", "")),
            default_max_price_per_1000=float(d.get("default_max_price_per_1000", 0.0)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name_es": self.name_es,
            "name_en": self.name_en,
            "icon": self.icon,
            "default_max_price_per_1000": self.default_max_price_per_1000,
        }

# =================================================================================================
# Stock
# =================================================================================================

@dataclass
class StockEntry:
    product_id: str
    qty_l: float
    max_price_per_1000: float
    cap_per_trip_l: float = 0.0
    min_keep_l: float = 0.0
    enabled_for_optimization: bool = True

    @staticmethod
    def from_dict(d: dict[str, Any]) -> StockEntry:
        return StockEntry(
            product_id=str(d.get("product_id", "")),
            qty_l=float(d.get("qty_l", 0.0)),
            max_price_per_1000=float(d.get("max_price_per_1000", 0.0)),
            cap_per_trip_l=float(d.get("cap_per_trip_l", 0.0)),
            min_keep_l=float(d.get("min_keep_l", 0.0)),
            enabled_for_optimization=bool(d.get("enabled_for_optimization", True)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "product_id": self.product_id,
            "qty_l": self.qty_l,
            "max_price_per_1000": self.max_price_per_1000,
            "cap_per_trip_l": self.cap_per_trip_l,
            "min_keep_l": self.min_keep_l,
            "enabled_for_optimization": self.enabled_for_optimization,
        }


# =================================================================================================
# Optimization models
# =================================================================================================

@dataclass(frozen=True)
class OptProduct:
    product_id: str
    stock_l: float
    min_keep_l: float
    cap_per_trip_l: float
    price_per_1000: float
    enabled: bool = True

@dataclass(frozen=True)
class TripPlanLine:
    product_id: str
    full_trips: int
    last_partial_used: bool
    sold_l: float
    revenue_eur: float

    @staticmethod
    def from_dict(d: dict[str, Any]) -> TripPlanLine:
        return TripPlanLine(
            product_id=str(d.get("product_id", "")),
            full_trips=int(d.get("full_trips", 0)),
            last_partial_used=bool(d.get("last_partial_used", False)),
            sold_l=float(d.get("sold_l", 0.0)),
            revenue_eur=float(d.get("revenue_eur", 0.0)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "product_id": self.product_id,
            "full_trips": self.full_trips,
            "last_partial_used": self.last_partial_used,
            "sold_l": self.sold_l,
            "revenue_eur": self.revenue_eur,
        }

@dataclass(frozen=True)
class TripPlan:
    feasible: bool
    target_eur: float
    total_revenue_eur: float
    total_trips: int
    lines: list[TripPlanLine]
    reason: str | None = None

    @staticmethod
    def from_dict(d: dict[str, Any]) -> TripPlan:
        lines_raw = d.get("lines", []) or []
        lines = [TripPlanLine.from_dict(x) for x in lines_raw if isinstance(x, dict)]
        return TripPlan(
            feasible=bool(d.get("feasible", False)),
            target_eur=float(d.get("target_eur", 0.0)),
            total_revenue_eur=float(d.get("total_revenue_eur", 0.0)),
            total_trips=int(d.get("total_trips", 0)),
            lines=lines,
            reason=d.get("reason"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "feasible": self.feasible,
            "target_eur": self.target_eur,
            "total_revenue_eur": self.total_revenue_eur,
            "total_trips": self.total_trips,
            "lines": [x.to_dict() for x in self.lines],
            "reason": self.reason,
        }

# =================================================================================================
# Farm data
# =================================================================================================

@dataclass
class FarmData:
    name: str
    stock: list[StockEntry]
    last_plan: TripPlan | None = None
    user_products: list[CatalogProduct] = field(default_factory=list)

    @staticmethod
    def from_dict(d: dict[str, Any], *, default_name: str = "Mi granja") -> FarmData:
        d = d or {}

        name = str(d.get("name") or default_name)

        stock_raw = d.get("stock") or []
        stock = [StockEntry.from_dict(x) for x in stock_raw if isinstance(x, dict)]

        plan_raw = d.get("last_plan")
        last_plan = TripPlan.from_dict(plan_raw) if isinstance(plan_raw, dict) else None

        user_products_raw = d.get("user_products") or []
        user_products = [
            CatalogProduct.from_dict(x) for x in user_products_raw if isinstance(x, dict)
        ]

        return FarmData(
            name=name,
            stock=stock,
            last_plan=last_plan,
            user_products=user_products,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "stock": [e.to_dict() for e in self.stock],
            "last_plan": (self.last_plan.to_dict() if self.last_plan is not None else None),
            "user_products": [p.to_dict() for p in self.user_products],
        }
