import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { SceneShot } from "./components/SceneShot";
import timing from "../../script/timing.json";

export const Play: React.FC = () => {
  const fps = timing.fps;

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {timing.scenes.map((scene) => {
        const fromFrame = Math.round(scene.start_sec * fps);
        const durationFrames = Math.max(1, Math.round(scene.duration_sec * fps));
        return (
          <Sequence
            key={scene.scene_id}
            from={fromFrame}
            durationInFrames={durationFrames}
          >
            <SceneShot scene={scene} fps={fps} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
