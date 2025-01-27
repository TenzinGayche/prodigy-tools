from pyannote.audio import Pipeline
from pydub import AudioSegment
import torchaudio
import os

upper_limit = 10
lower_limit = 2

def sec_to_millis(sec):
    return sec * 1000

def frame_to_sec(frame, sr):
    return frame / sr

def sec_to_frame(sec, sr):
    return sec * sr

HYPER_PARAMETERS = {
    # onset/offset activation thresholds
    "onset": 0.5,
    "offset": 0.5,
    # remove speech regions shorter than that many seconds.
    "min_duration_on": 2.0,
    # fill non-speech regions shorter than that many seconds.
    "min_duration_off": 0.0,
}

pipeline = Pipeline.from_pretrained(
    # "pyannote/voice-activity-detection",
    "config.yaml"
    # use_auth_token="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",
)
pipeline.instantiate(HYPER_PARAMETERS)

def save_segment(segment,folder,prefix, id, start_ms, end_ms):
    segment.export(f"./{folder}/{prefix}_{id:04}_{int(start_ms)}_to_{int(end_ms)}.mp3", format="mp3", parameters=["-ac", "1", "-ar", "16000"])

def delete_file(file):
    os.remove(file)


def split_audio(audio_file, output_folder):
    """splits the full audio file into segments based on
    Voice Activity Detection
    librosa split based on volume and
    blind chop to fit the range of upper_limit to lower_limit

    Args:
        audio_file (str): path to full audio file
        output_folder (str): where to store the split segments
    """
    print(f"{audio_file} {output_folder}")
    vad = pipeline(audio_file)
    original_audio_segment = AudioSegment.from_file(audio_file)
    original_audio_ndarray, sampling_rate = torchaudio.load(audio_file)
    original_audio_ndarray = original_audio_ndarray[0]
    counter = 1
    for vad_span in vad.get_timeline().support():
        vad_segment = original_audio_segment[sec_to_millis(vad_span.start) : sec_to_millis(vad_span.end)]
        vad_span_length = vad_span.end - vad_span.start
        if vad_span_length >= lower_limit and vad_span_length <= upper_limit:
            print(f"{counter} {vad_span_length} vad")
            save_segment(segment=vad_segment, folder=output_folder, prefix=output_folder, id=counter, start_ms=sec_to_millis(vad_span.start), end_ms=sec_to_millis(vad_span.end))
            counter += 1
        elif vad_span_length > upper_limit:
            cut = 2
            chop_length = vad_span_length / cut
            while chop_length > upper_limit:
                chop_length = vad_span_length / cut
                cut += 1
            for j in range(int(vad_span_length / chop_length)):
                segment_split_chop = original_audio_segment[sec_to_millis(vad_span.start + chop_length * j) : sec_to_millis(vad_span.start + chop_length * (j + 1))]
                print(f"{counter} {chop_length} chop")
                save_segment(segment=segment_split_chop, folder=output_folder, prefix=output_folder, id=counter, start_ms=sec_to_millis(vad_span.start + chop_length * j ), end_ms=sec_to_millis(vad_span.start + chop_length * ( j + 1 )))
                counter += 1
            # non_mute_segment_splits = librosa.effects.split(original_audio_ndarray[int(sec_to_frame(vad_span.start, sampling_rate)) : int(sec_to_frame(vad_span.end, sampling_rate))], top_db=30)
            # for split_start, split_end in non_mute_segment_splits:
            #     segment_split = original_audio_segment[sec_to_millis(vad_span.start + frame_to_sec(split_start, sampling_rate)) : sec_to_millis(vad_span.start + frame_to_sec(split_end, sampling_rate))]
            #     segment_split_duration = ((vad_span.start + frame_to_sec(split_end, sampling_rate)) - (vad_span.start + frame_to_sec(split_start, sampling_rate) ))
            #     if segment_split_duration >= lower_limit and segment_split_duration <= upper_limit:
            #         print(f"{counter} {segment_split_duration} split")
            #         save_segment(segment=segment_split, folder=output_folder, prefix=output_folder, id=counter, start_ms=sec_to_millis(vad_span.start + frame_to_sec(split_start, sampling_rate)), end_ms=sec_to_millis(vad_span.start + frame_to_sec(split_end, sampling_rate)))
            #         counter += 1
            #     elif segment_split_duration > upper_limit:
                    # chop_length = segment_split_duration / 2
                    # while chop_length > upper_limit:
                    #     chop_length = chop_length / 2
                    # for j in range(int(segment_split_duration / chop_length)):
                    #     segment_split_chop = original_audio_segment[sec_to_millis(vad_span.start + chop_length * j) : sec_to_millis(vad_span.start + chop_length * (j + 1))]
                    #     print(f"{counter} {chop_length} chop")
                    #     save_segment(segment=segment_split_chop, folder=output_folder, prefix=output_folder, id=counter, start_ms=sec_to_millis(vad_span.start + chop_length * j ), end_ms=sec_to_millis(vad_span.start + chop_length * ( j + 1 )))
                    #     counter += 1

if __name__ == "__main__":
    stt_folders = [filename for filename in os.listdir(".") if filename.startswith("STT_CS") and os.path.isdir(filename)]
    # print(stt_folders)
    for stt_folder in stt_folders:
        if len([name for name in os.listdir(stt_folder)]) == 1:
            print(stt_folder)
            split_audio(audio_file=f"./{stt_folder}/{stt_folder}.mp3", output_folder=stt_folder)
            # delete_file(file=f"./{stt_folder}/{stt_folder}.mp3")
