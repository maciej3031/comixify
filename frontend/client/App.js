import React from "react";
import ReactDOM from "react-dom";
import YouTube from 'react-youtube';
import { post } from "axios";
import Dropzone from "react-dropzone";
import { BarLoader } from "react-spinners";
import { css } from "react-emotion";

import {
	COMIXIFY_API,
	MAX_FILE_SIZE,
	PERMITTED_VIDEO_EXTENSIONS,
    FROM_YOUTUBE_API
} from "./constants";

class App extends React.Component {
	static appStates = {
		INITIAL: 0,
		PROCESSING: 1,
		FINISHED: 2,
		UPLOAD_ERROR: 3,
		DROP_ERROR: 4,
		SAMPLE_PROCESSING: 5
	};
	ytInput = React.createRef();
	constructor(props) {
		super(props);
		this.state = {
			state: App.appStates.INITIAL,
			videoId: null,
			drop_errors: [],
			result_comics: null,
            framesMode: "0",
            rlMode: "0",
            imageAssessment: "0"
		};
		this.onVideoDrop = this.onVideoDrop.bind(this);
        this.onModelChange = this.onModelChange.bind(this);
        this.handleResponse = this.handleResponse.bind(this);
        this.onYouTubeSubmit = this.onYouTubeSubmit.bind(this);
        this.onSamplingChange = this.onSamplingChange.bind(this);
        this.onImageAssessmentChange = this.onImageAssessmentChange.bind(this);
	}
	static onVideoUploadProgress(progressEvent) {
		let percentCompleted = Math.round(
			progressEvent.loaded * 100 / progressEvent.total
		);
		console.log(percentCompleted);
	}
	onModelChange(e) {
        let value = e.currentTarget.value;
	    this.setState({
            rlMode: value
        })
    }
	onSamplingChange(e) {
	    let value = e.currentTarget.value;
	    this.setState({
            framesMode: value
        })
    }
    onImageAssessmentChange(e) {
        let value = e.currentTarget.value;
        this.setState({
            imageAssessment: value
        })
    }
	handleResponse(res) {
	    if (res.data["status_message"] === "ok") {
            this.setState({
                state: App.appStates.FINISHED,
                result_comics: res.data["comic"]
            });
        } else {
            this.setState({
                state: App.appStates.UPLOAD_ERROR
            });
        }
    }
	processVideo(video) {
		let { framesMode, rlMode, imageAssessment } = this.state;
		let data = new FormData();
		data.append("file", video);
		data.set('frames_mode', parseInt(framesMode));
		data.set('rl_mode', parseInt(rlMode));
		data.set("image_assessment_mode", parseInt(imageAssessment));
		post(COMIXIFY_API, data, {
			headers: { "content-type": "multipart/form-data" },
			onUploadProgress: App.onVideoUploadProgress
		})
			.then(this.handleResponse)
			.catch(err => {
				console.error(err);
				this.setState({
					state: App.appStates.UPLOAD_ERROR
				});
			});
		this.setState({
			state: App.appStates.PROCESSING
		});
	}
	onVideoDrop(files, rejected) {
		if (rejected.length !== 0) {
			console.error(rejected);
			this.setState({
				drop_errors: ["Maximum size for single video is 50MB"],
				state: App.appStates.DROP_ERROR
			});
			return;
		}
		this.processVideo(files[0]);
	}
	submitYouTube(link) {
	    let { framesMode, rlMode, imageAssessment } = this.state;
	    post(FROM_YOUTUBE_API, {
		    url: link,
			frames_mode: parseInt(framesMode),
			rl_mode: parseInt(rlMode),
			image_assessment_mode: parseInt(imageAssessment)
        })
			.then(this.handleResponse)
			.catch(err => {
				console.error(err);
				this.setState({
					state: App.appStates.UPLOAD_ERROR
				});
			});
    }
	onYouTubeSubmit() {
		let ytLink = this.ytInput.current.value;
		this.submitYouTube(ytLink);
		this.setState({
			state: App.appStates.PROCESSING
		});
	}
	onSamplePlay(videoId) {
	    let link = "https://www.youtube.com/watch?v=" + videoId;
	    this.submitYouTube(link);
		this.setState({
			videoId: videoId,
			state: App.appStates.SAMPLE_PROCESSING
		});
	}
	render() {
		let {
		    state, drop_errors, result_comics, framesMode, rlMode, videoId, imageAssessment
		} = this.state;
		let showUsage = [
			App.appStates.INITIAL,
			App.appStates.UPLOAD_ERROR,
			App.appStates.DROP_ERROR,
			App.appStates.FINISHED
		].includes(state);
		let isProcessing = [
			App.appStates.SAMPLE_PROCESSING,
			App.appStates.PROCESSING
		].includes(state);
		return (
			<div>
				{state === App.appStates.FINISHED && [
					<img key="1" src={result_comics} />,
					<p key="2">Go again:</p>
				]}
				{state === App.appStates.DROP_ERROR &&
					drop_errors.map((o, i) => <p key={i}>{o}</p>)}
				{state === App.appStates.UPLOAD_ERROR && (
					<p>Server Error: Please try again later.</p>
				)}
				{showUsage && (
				    <div>
                        <div>Pipeline settings:</div>
                        <div>
                            <span>Frame sampling:</span>
                            <input
                                type="radio"
                                name="sampling"
                                id="sampling-0"
                                value="0"
                                checked={framesMode === "0"}
                                onChange={this.onSamplingChange}
                            />
                            <label htmlFor="sampling-0">2fps sampling</label>
                            <input
                                type="radio"
                                name="sampling"
                                id="sampling-1"
                                value="1"
                                checked={framesMode === "1"}
                                onChange={this.onSamplingChange}
                            />
                            <label htmlFor="sampling-1">I-frame sampling</label>
                        </div>
                        <div>
                            <span>Extraction model:</span>
                            <input
                                type="radio"
                                name="model"
                                id="model-0"
                                value="0"
                                checked={rlMode === "0"}
                                onChange={this.onModelChange}
                            />
                            <label htmlFor="model-0">Basic model</label>
                            <input
                                type="radio"
                                name="model"
                                id="model-1"
                                value="1"
                                checked={rlMode === "1"}
                                onChange={this.onModelChange}
                            />
                            <label htmlFor="model-1">+VTW model</label>
                        </div>
						<div>
                            <span>Image assessment:</span>
                            <input
                                type="radio"
                                name="image-assessment"
                                id="image-assessment-0"
                                value="0"
                                checked={imageAssessment === "0"}
                                onChange={this.onImageAssessmentChange}
                            />
							<label htmlFor="image-assessment-0">NIMA</label>
                            <input
                                type="radio"
                                name="image-assessment"
                                id="image-assessment-1"
                                value="1"
                                checked={imageAssessment === "1"}
                                onChange={this.onImageAssessmentChange}
                            />
                            <label htmlFor="image-assessment-1">Popularity</label>
                        </div>
                    </div>
				)}
				{showUsage && (
					<Dropzone
						onDrop={this.onVideoDrop}
						accept={PERMITTED_VIDEO_EXTENSIONS}
						maxSize={MAX_FILE_SIZE}
						className="dropzone"
						acceptClassName="dropzone--accepted"
						rejectClassName="dropzone--rejected"
						multiple={false} // Only one video at the time
					>
						<p>Drop video here, or click to select manually</p>
					</Dropzone>
				)}
				{showUsage && (
					<div>
						<label htmlFor="yt-link" className="yt-label">Or use YouTube link:</label>
						<input type="url" id="yt-link" ref={this.ytInput}/>
						<button onClick={this.onYouTubeSubmit}>Run</button>
						<div className="yt-clips-label">Or select one of sample videos:</div>
						<div className="youtube-clips">
                            <div>
                                <div className="yt-clip-label">Documentary</div>
                                <YouTube
                                    videoId="gr1ps0ooDhU"
                                    opts={{
                                        height: '90',
                                        width: '150',
                                    }}
                                    onPlay={this.onSamplePlay.bind(this, "gr1ps0ooDhU")}
                                />
                            </div>
                            <div>
                                <div className="yt-clip-label">Sports</div>
                                <YouTube
                                    videoId="MqqyD0nP1LQ"
                                    opts={{
                                        height: '90',
                                        width: '150',
                                    }}
                                    onPlay={this.onSamplePlay.bind(this, "MqqyD0nP1LQ")}
                                />
                            </div>
                            <div>
                                <div className="yt-clip-label">Music video</div>
                                <YouTube
                                    videoId="kJQP7kiw5Fk"
                                    opts={{
                                        height: '90',
                                        width: '150',
                                    }}
                                    onPlay={this.onSamplePlay.bind(this, "kJQP7kiw5Fk")}
                                />
                            </div>
                            <div>
                                <div className="yt-clip-label">Politics</div>
                                <YouTube
                                    videoId="F2b-2YnfZso"
                                    opts={{
                                        height: '90',
                                        width: '150',
                                    }}
                                    onPlay={this.onSamplePlay.bind(this, "F2b-2YnfZso")}
                                />
						    </div>
						</div>
					</div>
				)}
				{state === App.appStates.SAMPLE_PROCESSING && (
					<YouTube
						videoId={videoId}
						opts={{
							height: '390',
							width: '640',
							playerVars: {
								autoplay: 1
							}
						}}
					/>
				)}
				{isProcessing && (
					<BarLoader
						color={"rgb(54, 215, 183)"}
						className={css`
							margin: 20px auto 0 auto;
						`}
						width={10}
						widthUnit="rem"
					/>
				)}
			</div>
		);
	}
}

ReactDOM.render(<App />, document.getElementById("demo"));
