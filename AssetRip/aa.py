s = [
    {
        "name": "idle_v020000",
        "boundsData": {
            "Array": [
                {"x": -0.0390625, "y": 0.17187499, "z": 0},
                {"x": 0.89062494, "y": 1.0937499, "z": 0},
            ]
        },
        "untrimmedBoundsData": {
            "Array": [
                {"x": 0, "y": -0.0078125, "z": 0},
                {"x": 1.96875, "y": 2.609375, "z": 0},
            ]
        },
        "texelSize": {"x": 0.015625, "y": 0.015625},
        "positions": {
            "Array": [
                {"x": -0.48437497, "y": -0.37499997, "z": 0},
                {"x": 0.40624997, "y": -0.37499997, "z": 0},
                {"x": -0.48437497, "y": 0.71874994, "z": 0},
                {"x": 0.40624997, "y": 0.71874994, "z": 0},
            ]
        },
        "normals": {"Array": []},
        "tangents": {"Array": []},
        "uvs": {
            "Array": [
                {"x": 0.13281299, "y": 0.57373095},
                {"x": 0.13281299, "y": 0.601562},
                {"x": 0.1669917, "y": 0.57373095},
                {"x": 0.1669917, "y": 0.601562},
            ]
        },
        "normalizedUvs": {
            "Array": [
                {"x": 0, "y": 0},
                {"x": 0, "y": 1},
                {"x": 1, "y": 0},
                {"x": 1, "y": 1},
            ]
        },
        "indices": {"Array": [0, 3, 1, 2, 3, 0]},
        "material": {"m_FileID": 0, "m_PathID": 17},
        "materialId": 0,
        "sourceTextureGUID": "eb5d77e79c0ed4b4386dae1841d2fb3d",
        "extractRegion": 0,
        "regionX": 0,
        "regionY": 0,
        "regionW": 0,
        "regionH": 0,
        "flipped": 1,
        "complexGeometry": 0,
        "physicsEngine": 1,
        "colliderType": 0,
        "customColliders": {"Array": []},
        "colliderVertices": {"Array": []},
        "colliderIndicesFwd": {"Array": []},
        "colliderIndicesBack": {"Array": []},
        "colliderConvex": 0,
        "colliderSmoothSphereCollisions": 0,
        "polygonCollider2D": {"Array": []},
        "edgeCollider2D": {"Array": []},
        "attachPoints": {"Array": []},
    },
    {
        "name": "idle0008",
        "boundsData": {
            "Array": [
                {"x": -0.015625, "y": 0.1875, "z": 0},
                {"x": 1.3125, "y": 1.53125, "z": 0},
            ]
        },
        "untrimmedBoundsData": {
            "Array": [
                {"x": 0, "y": -0.0078125, "z": 0},
                {"x": 1.96875, "y": 2.609375, "z": 0},
            ]
        },
        "texelSize": {"x": 0.015625, "y": 0.015625},
        "positions": {
            "Array": [
                {"x": -0.671875, "y": -0.578125, "z": 0},
                {"x": 0.640625, "y": -0.578125, "z": 0},
                {"x": -0.671875, "y": 0.953125, "z": 0},
                {"x": 0.640625, "y": 0.953125, "z": 0},
            ]
        },
        "normals": {"Array": []},
        "tangents": {"Array": []},
        "uvs": {
            "Array": [
                {"x": 0.9238286, "y": 0.8066411},
                {"x": 0.9648433, "y": 0.8066411},
                {"x": 0.9238286, "y": 0.8544917},
                {"x": 0.9648433, "y": 0.8544917},
            ]
        },
        "normalizedUvs": {
            "Array": [
                {"x": 0, "y": 0},
                {"x": 1, "y": 0},
                {"x": 0, "y": 1},
                {"x": 1, "y": 1},
            ]
        },
        "indices": {"Array": [0, 3, 1, 2, 3, 0]},
        "material": {"m_FileID": 0, "m_PathID": 17},
        "materialId": 0,
        "sourceTextureGUID": "e2c80432751f709478ed004bab35d239",
        "extractRegion": 0,
        "regionX": 0,
        "regionY": 0,
        "regionW": 0,
        "regionH": 0,
        "flipped": 0,
        "complexGeometry": 0,
        "physicsEngine": 1,
        "colliderType": 0,
        "customColliders": {"Array": []},
        "colliderVertices": {"Array": []},
        "colliderIndicesFwd": {"Array": []},
        "colliderIndicesBack": {"Array": []},
        "colliderConvex": 0,
        "colliderSmoothSphereCollisions": 0,
        "polygonCollider2D": {"Array": []},
        "edgeCollider2D": {"Array": []},
        "attachPoints": {"Array": []},
    },
]


def p(xyz):
    return (xyz["x"] * 64, xyz["y"] * 64)


for s in s:
    for k in ["boundsData", "untrimmedBoundsData"]:
        a, b = map(p, s[k]["Array"])
        # a = middle pos
        # b = total size
        print(k, a, b)
    print()
