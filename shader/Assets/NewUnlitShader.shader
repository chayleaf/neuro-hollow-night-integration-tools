Shader "Unlit/NewUnlitShader" {
    Properties {  
        _Size("size", Range(0, 0.5)) = 0.5
        _Width("width", Range(0, 0.5)) = 0.1
        _Feather("feather", Range(0, 0.1)) = 0.1
        _Color("color", COLOR) = (1, 1, 1, 1)
    }
    SubShader {
        Tags { "Queue"="Transparent" "RenderType"="Transparent" }
        ZWrite Off
        ZTest LEqual
        Cull Off
        Pass {
            Blend SrcAlpha OneMinusSrcAlpha
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            struct appdata { float4 vertex : POSITION; };
            struct v2f { float4 vertex : SV_POSITION; float4 position: TEXCOORD1; };
            
            half _Size; half _Width; half _Feather; float4 _Color;

            v2f vert(appdata v) {
                v2f o; o.vertex = UnityObjectToClipPos(v.vertex); o.position = v.vertex;
                return o;
            }

            fixed4 frag(v2f v) : SV_Target {
                float o = _Size, i = _Size - _Width, f = _Feather, p = length(v.position.xy);
                float a = _Color.a * smoothstep(i, i + f, p) * (1.0 - smoothstep(o - f, o, p));
                return fixed4(_Color.rgb, a);
            }
            ENDCG
        }
    }
}
