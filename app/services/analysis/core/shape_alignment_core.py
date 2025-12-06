import numpy as np

# -------------------------------
# 유틸: 값들을 TH 기준으로 클러스터링
# -------------------------------
def cluster(values, TH=20):
    values_sorted = sorted(values)
    if not values_sorted:
        return []
    clusters = [[values_sorted[0]]]
    for v in values_sorted[1:]:
        if abs(v - clusters[-1][-1]) <= TH:
            clusters[-1].append(v)
        else:
            clusters.append([v])
    return clusters


# -------------------------------
# 패턴 감지
# -------------------------------
def detect_pattern(shapes):
    """
    shapes: [{id, left, top, ...}]
    return "horizontal" | "vertical" | "grid" | "unknown"
    """

    tops = np.array([s["top"] for s in shapes], dtype=float)
    lefts = np.array([s["left"] for s in shapes], dtype=float)

    TH = 20

    # --------------------------
    # Grid 감지용 클러스터링
    # --------------------------
    def cluster(values):
        values_sorted = sorted(values)
        clusters = [[values_sorted[0]]]
        for v in values_sorted[1:]:
            if abs(v - clusters[-1][-1]) <= TH:
                clusters[-1].append(v)
            else:
                clusters.append([v])
        return clusters

    top_clusters = cluster(tops)
    left_clusters = cluster(lefts)

    # --------------------------
    # ✔ 강화된 Grid 판단 기준 적용
    # --------------------------
    if len(shapes) >= 4:  # 최소 2×2 가능할 때만 grid 고려
        # row/col 중 실제 2개 이상 갖춘 row/col 개수 계산
        valid_row_count = sum(1 for c in top_clusters if len(c) >= 2)
        valid_col_count = sum(1 for c in left_clusters if len(c) >= 2)

        # 반드시 row, col 둘 다 2개 이상 존재해야 grid
        if valid_row_count >= 2 and valid_col_count >= 2:
            return "grid"

    # --------------------------
    # Horizontal / Vertical 감지
    # --------------------------
    top_std = float(np.std(tops))
    left_std = float(np.std(lefts))

    is_horizontal = top_std < TH
    is_vertical = left_std < TH

    if is_horizontal and not is_vertical:
        return "horizontal"
    if is_vertical and not is_horizontal:
        return "vertical"

    # 둘 다 만족/불만족 = 애매 → unknown
    return "unknown"


# -------------------------------
# 패턴별 좌표 조정
# -------------------------------
def adjust_horizontal(shapes):
    """
    수평 패턴:
    - 모든 top을 거의 같은 값으로 맞추고,
    - left 사이 간격을 균일하게 재배치
    """
    if len(shapes) <= 1:
        return shapes

    shapes_sorted = sorted(shapes, key=lambda s: s["left"])
    top_mean = float(np.mean([s["top"] for s in shapes_sorted]))

    xs = [s["left"] for s in shapes_sorted]
    first_left = xs[0]
    spacing = (xs[-1] - xs[0]) / (len(shapes_sorted) - 1) if len(shapes_sorted) > 1 else 0

    new_shapes = []
    for i, s in enumerate(shapes_sorted):
        new_shapes.append({
            **s,
            "top": top_mean,
            "left": first_left + i * spacing,
        })
    return new_shapes


def adjust_vertical(shapes):
    """
    수직 패턴:
    - 모든 left를 거의 같은 값으로 맞추고,
    - top 사이 간격을 균일하게 재배치
    """
    if len(shapes) <= 1:
        return shapes

    shapes_sorted = sorted(shapes, key=lambda s: s["top"])
    left_mean = float(np.mean([s["left"] for s in shapes_sorted]))

    ys = [s["top"] for s in shapes_sorted]
    first_top = ys[0]
    spacing = (ys[-1] - ys[0]) / (len(shapes_sorted) - 1) if len(shapes_sorted) > 1 else 0

    new_shapes = []
    for i, s in enumerate(shapes_sorted):
        new_shapes.append({
            **s,
            "left": left_mean,
            "top": first_top + i * spacing,
        })
    return new_shapes


def adjust_grid(shapes, TH=20):
    """
    Grid 패턴:
    - top 기준으로 row 를 나누고,
    - 각 row 안에서는 수평 정렬 + 균등 간격
    """
    if len(shapes) <= 1:
        return shapes

    # top 기준으로 정렬
    shapes_sorted = sorted(shapes, key=lambda s: s["top"])
    tops = [s["top"] for s in shapes_sorted]

    # row split: top 차이가 TH 보다 크면 다른 row 로 본다
    row_indices = [0]
    for i in range(1, len(shapes_sorted)):
        if abs(tops[i] - tops[i - 1]) > TH:
            row_indices.append(i)
    row_indices.append(len(shapes_sorted))

    rows = []
    for i in range(len(row_indices) - 1):
        start = row_indices[i]
        end = row_indices[i + 1]
        rows.append(shapes_sorted[start:end])

    adjusted = []
    for row in rows:
        adjusted.extend(adjust_horizontal(row))

    return adjusted


# -------------------------------
# deprecated 함수
# -------------------------------
def adjust_shapes(shapes):
    pattern = detect_pattern(shapes)
    print(f"Detected pattern: {pattern}")

    if pattern == "horizontal":
        return adjust_horizontal(shapes)
    elif pattern == "vertical":
        return adjust_vertical(shapes)
    elif pattern == "grid":
        return adjust_grid(shapes)
    else:
        # unknown 은 건드리지 않고 그대로 반환
        return shapes
    
# -------------------------------
# 패턴에 따른 조정 함수
# -------------------------------
def adjust_shapes_with_pattern(pattern, shapes):
    if pattern == "horizontal":
        return adjust_horizontal(shapes)
    elif pattern == "vertical":
        return adjust_vertical(shapes)
    elif pattern == "grid":
        return adjust_grid(shapes)
    else:
        return shapes
