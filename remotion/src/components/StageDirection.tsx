import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

const FADE_FRAMES = 12; // 0.4s @ 30fps

export const StageDirection: React.FC<{
  text: string;
  durationFrames: number;
}> = ({ text, durationFrames }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(
    frame,
    [
      0,
      Math.min(FADE_FRAMES, Math.floor(durationFrames / 2)),
      Math.max(0, durationFrames - FADE_FRAMES),
      durationFrames,
    ],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        opacity,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          maxWidth: "70%",
          padding: "28px 44px",
          backgroundColor: "rgba(0, 0, 0, 0.55)",
          color: "#f0e6d2",
          fontFamily:
            "'Malgun Gothic', 'Apple SD Gothic Neo', 'Noto Sans CJK KR', serif",
          fontSize: 34,
          fontStyle: "italic",
          lineHeight: 1.5,
          letterSpacing: 1,
          textAlign: "center",
          textShadow: "0 1px 6px rgba(0, 0, 0, 0.7)",
          borderRadius: 4,
          borderLeft: "2px solid rgba(240, 230, 210, 0.5)",
          borderRight: "2px solid rgba(240, 230, 210, 0.5)",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
