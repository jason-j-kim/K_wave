import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile } from "remotion";
import { SceneShot } from "./components/SceneShot";
import { TitleCard } from "./components/TitleCard";
import type { Timing } from "./types";
import timingData from "../../script/timing.json";

const timing = timingData as unknown as Timing;

const toFrames = (sec: number, fps: number) => Math.max(1, Math.round(sec * fps));

export const Play: React.FC = () => {
  const fps = timing.fps;

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {timing.ambience && timing.ambience.available ? (
        <Audio
          src={staticFile(timing.ambience.file)}
          loop
          volume={timing.ambience.volume}
        />
      ) : null}

      {timing.intro ? (
        <Sequence
          from={Math.round(timing.intro.start_sec * fps)}
          durationInFrames={toFrames(timing.intro.duration_sec, fps)}
        >
          <TitleCard
            title={timing.intro.title}
            subtitle={timing.intro.subtitle}
            durationFrames={toFrames(timing.intro.duration_sec, fps)}
            fadeInFrames={toFrames(timing.intro.fade_in_sec, fps)}
            fadeOutFrames={toFrames(timing.intro.fade_out_sec, fps)}
            variant="intro"
          />
        </Sequence>
      ) : null}

      {timing.scenes.map((scene) => (
        <Sequence
          key={scene.scene_id}
          from={Math.round(scene.start_sec * fps)}
          durationInFrames={toFrames(scene.duration_sec, fps)}
        >
          <SceneShot scene={scene} fps={fps} />
        </Sequence>
      ))}

      {timing.outro ? (
        <Sequence
          from={Math.round(timing.outro.start_sec * fps)}
          durationInFrames={toFrames(timing.outro.duration_sec, fps)}
        >
          <TitleCard
            title={timing.outro.title}
            subtitle={timing.outro.subtitle}
            durationFrames={toFrames(timing.outro.duration_sec, fps)}
            fadeInFrames={toFrames(timing.outro.fade_in_sec, fps)}
            fadeOutFrames={toFrames(timing.outro.fade_out_sec, fps)}
            variant="outro"
          />
        </Sequence>
      ) : null}
    </AbsoluteFill>
  );
};
