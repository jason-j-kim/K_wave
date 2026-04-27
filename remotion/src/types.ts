export type DialogueLine = {
  type: "dialogue";
  line_id: string;
  speaker: string;
  text: string;
  audio: string;
  start_sec_in_scene: number;
  duration_sec: number;
};

export type StageDirectionLine = {
  type: "stage_direction";
  line_id: string;
  speaker: null;
  text: string;
  start_sec_in_scene: number;
  duration_sec: number;
};

export type Line = DialogueLine | StageDirectionLine;

export type Scene = {
  scene_id: number;
  title: string;
  setting: string;
  image: string;
  start_sec: number;
  duration_sec: number;
  lines: Line[];
};

export type TitleSpec = {
  start_sec: number;
  duration_sec: number;
  fade_in_sec: number;
  fade_out_sec: number;
  title: string;
  subtitle: string;
};

export type AmbienceSpec = {
  file: string;
  volume: number;
  available: boolean;
};

export type Timing = {
  fps: number;
  width: number;
  height: number;
  gap_between_lines_sec: number;
  gap_between_scenes_sec: number;
  intro: TitleSpec | null;
  outro: TitleSpec | null;
  ambience: AmbienceSpec | null;
  total_duration_sec: number;
  total_duration_frames: number;
  scenes: Scene[];
};
