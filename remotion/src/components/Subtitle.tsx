import React from "react";
import { AbsoluteFill } from "remotion";

export const Subtitle: React.FC<{ text: string; speaker: string }> = ({
  text,
  speaker,
}) => {
  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: 80,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          maxWidth: "70%",
          padding: "20px 32px",
          backgroundColor: "rgba(0, 0, 0, 0.6)",
          color: "white",
          fontFamily:
            "'Malgun Gothic', 'Apple SD Gothic Neo', 'Noto Sans CJK KR', sans-serif",
          fontSize: 36,
          lineHeight: 1.4,
          textAlign: "center",
          textShadow: "0 1px 4px rgba(0, 0, 0, 0.6)",
          borderRadius: 8,
        }}
      >
        <div
          style={{
            fontSize: 22,
            color: "#ddd",
            opacity: 0.85,
            marginBottom: 6,
            fontStyle: "italic",
            letterSpacing: 1,
          }}
        >
          {speaker}
        </div>
        {text}
      </div>
    </AbsoluteFill>
  );
};
