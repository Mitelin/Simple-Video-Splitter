"""Build FFmpeg argument lists for splitting a source video into two parts."""

from __future__ import annotations

from VideoSplitter.Models.split_request import SplitRequest


class FfmpegCommandBuilder:
    """Create FFmpeg command fragments for legacy and current split workflows."""

    def build_filter_complex(self, split_seconds: int) -> str:
        """Build the legacy two-output filter graph kept for compatibility and tests."""

        return (
            "[0:v]split=2[v1][v2];"
            "[0:a]asplit=2[a1][a2];"
            f"[v1]trim=start=0:end={split_seconds},setpts=PTS-STARTPTS[v1o];"
            f"[a1]atrim=start=0:end={split_seconds},asetpts=PTS-STARTPTS[a1o];"
            f"[v2]trim=start={split_seconds},setpts=PTS-STARTPTS[v2o];"
            f"[a2]atrim=start={split_seconds},asetpts=PTS-STARTPTS[a2o]"
        )

    def build_output_filter_complex(self, split_seconds: int, output_index: int) -> str:
        """Build a single-output trim graph for the requested half of the video."""

        if output_index == 1:
            return (
                f"[0:v]trim=start=0:end={split_seconds},setpts=PTS-STARTPTS[vout];"
                f"[0:a]atrim=start=0:end={split_seconds},asetpts=PTS-STARTPTS[aout]"
            )

        if output_index == 2:
            return (
                f"[0:v]trim=start={split_seconds},setpts=PTS-STARTPTS[vout];"
                f"[0:a]atrim=start={split_seconds},asetpts=PTS-STARTPTS[aout]"
            )

        raise ValueError("output_index must be 1 or 2")

    def build_output_arguments(self, request: SplitRequest, output_index: int) -> list[str]:
        """Build FFmpeg arguments for one phase of the sequential split process."""

        output_path = request.output_path_1 if output_index == 1 else request.output_path_2
        timing_arguments = ["-i", request.input_path]

        if output_index == 1:
            timing_arguments.extend(["-t", request.split_time_text])
        elif output_index == 2:
            timing_arguments = ["-ss", request.split_time_text, "-i", request.input_path]
        else:
            raise ValueError("output_index must be 1 or 2")

        return [
            "-y",
            "-progress",
            "pipe:1",
            "-nostats",
            *timing_arguments,
            "-map",
            "0:v:0",
            "-map",
            "0:a:0",
            "-c:v",
            request.video_codec,
            "-crf",
            str(request.crf),
            "-preset",
            request.preset,
            "-c:a",
            request.audio_codec,
            "-b:a",
            request.audio_bitrate,
            output_path,
        ]

    def build_arguments(self, request: SplitRequest) -> list[str]:
        """Build the legacy one-command argument list that renders both outputs at once."""

        filter_complex = self.build_filter_complex(request.split_seconds)
        return [
            "-y",
            "-progress",
            "pipe:1",
            "-nostats",
            "-i",
            request.input_path,
            "-filter_complex",
            filter_complex,
            "-map",
            "[v1o]",
            "-map",
            "[a1o]",
            "-c:v",
            request.video_codec,
            "-crf",
            str(request.crf),
            "-preset",
            request.preset,
            "-c:a",
            request.audio_codec,
            "-b:a",
            request.audio_bitrate,
            request.output_path_1,
            "-map",
            "[v2o]",
            "-map",
            "[a2o]",
            "-c:v",
            request.video_codec,
            "-crf",
            str(request.crf),
            "-preset",
            request.preset,
            "-c:a",
            request.audio_codec,
            "-b:a",
            request.audio_bitrate,
            request.output_path_2,
        ]
