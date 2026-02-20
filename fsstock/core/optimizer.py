import heapq
from typing import Any

from .models import OptProduct, TripPlan, TripPlanLine


# =================================================================================================
# Helpers 
# =================================================================================================

def _init_state(products: list[OptProduct]) -> dict[str, dict]:
    """
    Builds the state per product, respecting minimums and rules:
    - full trips: floor(sealable/cap)
    - last trip: rem (only available after full trips are sold out, or if there is no full trip)
    
    Parameters
    ----------
    products: List[OptProduct]
        List of products in stock
    
    Returns
    -------
    st: dict[str, dict]
        Dictionary where each key is the product id, and values are
        dictionaries containing the following items:
        - product_id: str
            Product ID
        - stock_l: float
            Current stock of product
        - min_keep_l: float
            Minimum amount that there has to be in stock
        - cap_l: float
            Capacity of a trip
        - p_per_l: float
            Price per liter (€/L)
        - sellable_l: float
            Sellable quantity: stock_l - min_keep_l
        - remaining_full: int
            Number of full trips remaining
        - rem_l: float
            Remaining amount of product (L)
        - last_used: bool
            If the last trip (remaining) has been used
        - sold_l: float
            Total L sold
        - chosen_full: int
            Number of full trips used
        - chosen_last: bool
            If the last trip (remaining) has been used
    """
    st: dict[str, dict] = {}
    for pr in products:
        # If available (enabled for optimization, exist capacity and enough stock), skip
        if not pr.enabled or pr.cap_per_trip_l <= 0 or pr.stock_l <= pr.min_keep_l:
            continue

        sellable_l: float = pr.stock_l - pr.min_keep_l
        p_per_l: float = pr.price_per_1000 / 1000.0
        cap_l: float = pr.cap_per_trip_l
        m_full: int = sellable_l // cap_l
        rem_l: float = sellable_l - m_full * cap_l  # 0 <= rem < cap

        st[pr.product_id] = {
            "product_id": pr.product_id,
            "stock_l": pr.stock_l,
            "min_keep_l": pr.min_keep_l,
            "cap": cap_l,
            "p_per_l": p_per_l,
            "sellable_l": sellable_l,
            "remaining_full": int(m_full),
            "rem_l": float(rem_l),
            "last_used": False,
            "sold_l": 0.0,
            "chosen_full": 0,
            "chosen_last": False,
        }
    return st

def _candidate_for_max_revenue(info: dict[str, Any]) -> tuple[float, str, str] | None:
    """
    Returns (value_eur, pid, kind) of the next available trip for this
    product in "maximize revenue" mode.
    
    Parameters
    ----------
    info: dict[str, Any]
        Dictionary containing the following items:
        - remaining_full: int
            Number of full trips remaining
        - rem_l: float
            Amount of remaining product after full trips (L)
        - last_used: bool
            If last trip is used
        - cap: float
            Capacity of a trip (L)
        - p_per_l: flat
            Price per liter (€/L)
        - product_id: str

    Returns
    -------
    tuple[float, str, str] | None
        float:
            Earnings for the best trip (€)
        str:
            Product ID of the best trip
        str:
            Type of trip: "full" or "last"
    """
    pid: str = info["product_id"]
    cap: float = info["cap"]
    p: float = info["p_per_l"]

    # If full trip is available, return it
    if info["remaining_full"] > 0:
        return (cap * p, pid, "full")

    # If there are no full trips available, return the last trip,
    # if it has not been useff
    if info["rem_l"] > 0 and not info["last_used"]:
        return (info["rem_l"] * p, pid, "last")

    return None

def _min_trips_needed(st: dict[str, dict], target_eur: float) -> int | None:
    """
    Returns the minimum number of trips K needed to reach target_eur,
    or None if it's impossible.
    Calculated using the maximum revenue per trip)
    
    Parameters
    ----------
    st: dict[str, dict]
        Initial state
    
    target_eur: float
        Minimum revenue
    
    Returns
    -------
        trips: int | None
            Minimum number of trips to reach quota.
            If total < target_eur, returns None
    """
    if target_eur <= 0:
        return 0

    # Simulation of "max revenue" until reaching quota
    tmp: dict[str, dict] = {
        pid: {
            "remaining_full": info["remaining_full"],
            "rem_l": info["rem_l"],
            "last_used": info["last_used"],
            "cap": info["cap"],
            "p_per_l": info["p_per_l"],
            "product_id": pid,
        }
        for pid, info in st.items()
    }

    heap: list[tuple[float, str, str]] = []
    for pid, info in tmp.items():
        cand: tuple[float, str, str] | None = _candidate_for_max_revenue(info)
        if cand:
            val, pid2, kind = cand
            heapq.heappush(heap, (-val, pid2, kind))  # Insert possible trip according priority

    total: float = 0.0
    trips: int = 0
    # Select trips until empty list or reach quota
    while heap and total < target_eur:
        neg_val, pid, kind = heapq.heappop(heap)
        val: float = -neg_val
        info: dict[str, Any] = tmp[pid]

        # Update 
        total += val
        trips += 1
        if kind == "full":
            info["remaining_full"] -= 1
        else:
            info["last_used"] = True

        # Update product (if remains)
        cand: tuple[float, str, str] | None = _candidate_for_max_revenue(info)
        if cand:
            val2, pid2, kind2 = cand
            heapq.heappush(heap, (-val2, pid2, kind2))
    
    # If quota not reached, return None,
    # Otherwise, return the number of trips
    if total < target_eur:
        return None
    return trips

def _max_revenue_possible(st: dict[str, dict], trips_left: int) -> float:
    """
    Calculates the maximum possible € with trips_left trips, starting
    from the current state.
    Respects the rule that last only appears when full trips are 
    exhausted.
    
    Parameters
    ----------
    st: dict[str, dict]
        Current state
    trips_left: int
        Number of trips left
    
    Returns
    -------
    float
        The maximum revenue possible
    """
    if trips_left <= 0:
        return 0.0

    # Lightweight copy of the minimum state necessary to simulate
    tmp: dict[str, dict] = {
        pid: {
            "remaining_full": info["remaining_full"],
            "rem_l": info["rem_l"],
            "last_used": info["last_used"],
            "cap": info["cap"],
            "p_per_l": info["p_per_l"],
            "product_id": pid,
        }
        for pid, info in st.items()
    }

    heap: list[tuple[float, str, str]] = []
    for pid, info in tmp.items():
        cand: tuple[float, str, str] | None = _candidate_for_max_revenue(info)
        if cand:
            val, pid2, kind = cand
            heapq.heappush(heap, (-val, pid2, kind))

    total: float = 0.0
    used: int = 0
    while heap and used < trips_left:
        neg_val, pid, kind = heapq.heappop(heap)
        val: float = -neg_val
        info: dict[str, Any] = tmp[pid]

        # Update
        total += val
        used += 1
        if kind == "full":
            info["remaining_full"] -= 1
        else:
            info["last_used"] = True

        # Insert the next candidate for this product
        cand = _candidate_for_max_revenue(info)
        if cand:
            val2, pid2, kind2 = cand
            heapq.heappush(heap, (-val2, pid2, kind2))

    return total



# =================================================================================================
# Main optimization
# =================================================================================================

def optimize_min_trips(products: list[OptProduct], target_eur: float) -> TripPlan:
    """
    Priority (lexicographical):
    1) Minimize the number of trips (minimum possible K).
    2) Maximize final remaining stock (prefer sales that leave more
    stock).
    Local comparison based on remaining stock after choosing the trip.
    3) Maximize total profit (only if 1) and 2) are tied).

    Trip Rule:
    - Trips filled with C_i liters.
    - A single "last" (partial) trip with rem_l liters, ONLY if there
    is no more for a full trip (i.e., after a full trip or if there was
    never a full trip).
    
    Parameters
    ----------
    products: list[OptProduct]
        List of all stocked products
    target_eur: float
        Minimum revenue
    
    Returns
    -------
    TripPlan:
        The plan that minimizes the number of trips, but ensures the
        minimum revenue
    """
    # If target <= 0, not selected plan
    if target_eur <= 0.0:
        return TripPlan(
            feasible=False,
            target_eur=target_eur,
            total_revenue_eur=0.0,
            total_trips=0,
            lines=[],
            reason="objective.plan_info.no_plan")

    # Initial state of products
    st: dict[str, dict] = _init_state(products)
    # If there are no eligible products
    if not st:
        return TripPlan(
            feasible=False,
            target_eur=target_eur,
            total_revenue_eur=0.0,
            total_trips=0,
            lines=[],
            reason="objective.plan_info.no_products",
        )

    # Minimize number of trips -> optimal number of trips K
    K: int | None = _min_trips_needed(st, target_eur)
    # target_eur > max revenue
    if K is None:
        max_all: float = _max_revenue_possible(st, 10**9)  # consume todo
        return TripPlan(
            feasible=False,
            target_eur=target_eur,
            total_revenue_eur=max_all,
            total_trips=0,
            lines=[],
            reason="objective.plan_info.not_reached_quota",
        )

    total: float = 0.0  # Total revenue
    trips_used: int = 0  # Total trips

    # We build exactly K trips with feasibility checks:
    # We choose the trip that leaves the most remaining stock, provided
    # we can still reach the target with the remaining trips.
    for step in range(1, K+1):
        trips_left_after: int = K - step  # Number of trips after this trip
        # Best product for this trip (ID, type (fulll, remaining), sold (L), sold (€))
        best_choice: tuple[str, str, float, float] | None = None
        # Best product for this trip (stock remaining after, value, ID)
        best_key: tuple[float, float, str] | None = None  

        # Generate current candidates
        for pid, info in st.items():
            # Are there full trips available?
            if info["remaining_full"] > 0:
                kind: str = "full"
                sold: float = info["cap"]
                value: float = sold * info["p_per_l"]
            # Is there the last trip available?
            elif (info["rem_l"] > 0) and (not info["last_used"]):
                kind: str = "last"
                sold: float = info["rem_l"]
                value: float = sold * info["p_per_l"]
            else:
                continue

            # Remaining stock if we choose this trip
            remaining_stock_after: float = info["stock_l"] - info["sold_l"] - sold

            # Apply election
            st_temp = st_temp = {k: v.copy() for k, v in st.items()}
            if kind == "full":
                st_temp[pid]["remaining_full"] -= 1
            else:
                st_temp[pid]["last_used"] = True
            # maximum possible € in what remains
            max_future: float = _max_revenue_possible(st_temp, trips_left_after)

            # Feasibility check: Can we still make it?
            if total + value + max_future < target_eur:
                continue

            # Selection Key
            # 1) highest remaining stock after
            # 2) highest value (earnings) as the final criterion
            # 3) stable PID
            key: tuple[float, float, str] = (remaining_stock_after, value, pid)
            if (best_key is None) or (key > best_key):  # Change of best item to sell in this trip
                best_key: tuple[float, float, str] = key
                best_choice: tuple[str, str, float, float] = (pid, kind, sold, value)

        # Apply the choice to the actual state
        pid, kind, sold, value = best_choice
        info: dict[str, Any] = st[pid]

        info["sold_l"] += sold
        total += value
        trips_used += 1
        if kind == "full":
            info["chosen_full"] += 1
            info["remaining_full"] -= 1
        else:
            info["chosen_last"] = True
            info["last_used"] = True

    # Build trip plan lines
    lines: list[TripPlanLine] = []
    for pid, info in st.items():
        # Skip unused products
        if info["chosen_full"] == 0 and not info["chosen_last"]:
            continue

        revenue: float = info["sold_l"] * info["p_per_l"]
        lines.append(
            TripPlanLine(
                product_id=pid,
                full_trips=info["chosen_full"],
                last_partial_used=info["chosen_last"],
                sold_l=info["sold_l"],
                revenue_eur=revenue,
            )
        )

    # Presentation: by trips, then by sold, etc.
    lines.sort(key=lambda x: (-x.full_trips - (1 if x.last_partial_used else 0), -x.sold_l, x.product_id))

    return TripPlan(
        feasible=True,
        target_eur=target_eur,
        total_revenue_eur=total,
        total_trips=trips_used,
        lines=lines,
    )
