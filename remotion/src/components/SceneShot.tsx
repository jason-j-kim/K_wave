import React from "react";
import { AbsoluteFill, Audio, Img, Sequence, staticFile } from "remotion";
import { Subtitle } from "./Subtitle";

type Line = {
  line_id: string;
  speaker: string;
  text: string;
  audio: string;
  start_sec_in_scene: number;
  duration_sec: number;
};

type Scene = {
  scene_id: number;
  title: string;
  setting: string;
  image: string;
  start_sec: number;
  duration_sec: number;
  lines: Line[];
};

export const SceneShot: React.FC<{ scene: Scene; fps: number }> = ({
  scene,
  fps,
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Img
        src={staticFile(`images/${scene.image}`)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
        }}
      />
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
            <Audio src={staticFile(`voices/${line.audio}`)} />
            <Subtitle text={line.text} speaker={line.speaker} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
