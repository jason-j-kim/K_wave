import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";
import type { Scene } from "../types";
import { Subtitle } from "./Subtitle";
import { StageDirection } from "./StageDirection";

const SCENE_FADE_FRAMES = 15; // 0.5s @ 30fps

export const SceneShot: React.FC<{ scene: Scene; fps: number }> = ({
  scene,
  fps,
}) => {
  const frame = useCurrentFrame();
  const sceneDurationFrames = Math.max(
    1,
    Math.round(scene.duration_sec * fps),
  );

  const sceneOpacity = interpolate(
    frame,
    [
      0,
      SCENE_FADE_FRAMES,
      Math.max(0, sceneDurationFrames - SCENE_FADE_FRAMES),
      sceneDurationFrames,
    ],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // Ken Burns: 장면 길이에 걸쳐 1.0 → 1.06 줌 + 좌우 살짝 드리프트.
  // scene_id 짝수/홀수에 따라 드리프트 방향을 교차해 단조로움 방지.
  const t = sceneDurationFrames > 1 ? frame / sceneDurationFrames : 0;
  const scale = interpolate(t, [0, 1], [1.0, 1.06]);
  const direction = scene.scene_id % 2 === 0 ? -1 : 1;
  const driftX = interpolate(t, [0, 1], [0, 24 * direction]);
  const driftY = interpolate(t, [0, 1], [0, -10]);

  return (
    <AbsoluteFill style={{ backgroundColor: "black", opacity: sceneOpacity }}>
      <AbsoluteFill style={{ overflow: "hidden" }}>
        <Img
          src={staticFile(`images/${scene.image}`)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform: `translate(${driftX}px, ${driftY}px) scale(${scale})`,
            transformOrigin: "center",
          }}
        />
      </AbsoluteFill>
      {scene.lines.map((line) => {
        const fromFrame = Math.round(line.start_sec_in_scene * fps);
        const durationFrames = Math.max(
          1,
          Math.round(line.duration_sec * fps),
        );
        return (
          <Sequence
            key={line.line_id}
            from={fromFrame}
            durationInFrames={durationFrames}
          >
            {line.type === "dialogue" ? (
              <>
                <Audio src={staticFile(`voices/${line.audio}`)} />
                <Subtitle text={line.text} speaker={line.speaker} />
              </>
            ) : (
              <StageDirection text={line.text} durationFrames={durationFrames} />
            )}
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
