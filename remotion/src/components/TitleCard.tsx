import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

export const TitleCard: React.FC<{
  title: string;
  subtitle: string;
  durationFrames: number;
  fadeInFrames: number;
  fadeOutFrames: number;
  variant?: "intro" | "outro";
}> = ({
  title,
  subtitle,
  durationFrames,
  fadeInFrames,
  fadeOutFrames,
  variant = "intro",
}) => {
  const frame = useCurrentFrame();

  const safeFadeIn = Math.min(fadeInFrames, Math.floor(durationFrames / 2));
  const safeFadeOut = Math.min(fadeOutFrames, Math.floor(durationFrames / 2));

  const opacity = interpolate(
    frame,
    [
      0,
      safeFadeIn,
      Math.max(safeFadeIn + 1, durationFrames - safeFadeOut),
      durationFrames,
    ],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  const titleSize = variant === "intro" ? 110 : 130;
  const subtitleSize = variant === "intro" ? 36 : 28;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "black",
        justifyContent: "center",
        alignItems: "center",
        opacity,
      }}
    >
      <div
        style={{
          fontFamily:
            "'Malgun Gothic', 'Apple SD Gothic Neo', 'Noto Serif KR', serif",
          color: "#f3ead2",
          fontSize: titleSize,
          fontWeight: 600,
          letterSpacing: 6,
          textAlign: "center",
          textShadow: "0 2px 12px rgba(0,0,0,0.6)",
          marginBottom: variant === "intro" ? 36 : 24,
        }}
      >
        {title}
      </div>
      {subtitle ? (
        <div
          style={{
            fontFamily:
              "'Malgun Gothic', 'Apple SD Gothic Neo', 'Noto Sans CJK KR', sans-serif",
            color: "#bbb1a0",
            fontSize: subtitleSize,
            fontStyle: "italic",
            letterSpacing: 3,
            textAlign: "center",
          }}
        >
          {subtitle}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
