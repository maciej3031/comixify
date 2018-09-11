import React from "react";
import ReactDOM from "react-dom";
import { post } from "axios";
import Dropzone from "react-dropzone";
import { BarLoader } from "react-spinners";
import { css } from "react-emotion";

import {
	COMIXIFY_API,
	MAX_FILE_SIZE,
	PERMITTED_VIDEO_EXTENSIONS
} from "./constants";

class App extends React.Component {
	static appStates = {
		INITIAL: 0,
		PROCESSING: 1,
		FINISHED: 2,
		UPLOAD_ERROR: 3,
		DROP_ERROR: 4
	};
	constructor(props) {
		super(props);
		this.state = {
			state: App.appStates.INITIAL,
			drop_errors: [],
			result_comics: null
		};
		this.onVideoDrop = this.onVideoDrop.bind(this);
		this.onVideoUploadProgress = this.onVideoUploadProgress.bind(this);
	}
	onVideoUploadProgress(progressEvent) {
		let percentCompleted = Math.round(
			progressEvent.loaded * 100 / progressEvent.total
		);
		console.log(percentCompleted);
	}
	processVideo(video) {
		let data = new FormData();
		data.append("file", video);
		post(COMIXIFY_API, data, {
			headers: { "content-type": "multipart/form-data" },
			onUploadProgress: this.onVideoUploadProgress
		})
			.then(res => {
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
			})
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
				stata: App.appStates.DROP_ERROR
			});
			return;
		}
		this.processVideo(files[0]);
	}

	render() {
		let { state, drop_errors, result_comics } = this.state;
		let showDropzone = [
			App.appStates.INITIAL,
			App.appStates.UPLOAD_ERROR,
			App.appStates.DROP_ERROR,
			App.appStates.FINISHED
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
				{showDropzone && (
					<Dropzone
						onDrop={this.onVideoDrop}
						accept={PERMITTED_VIDEO_EXTENSIONS}
						maxSize={MAX_FILE_SIZE}
						className="dropzone"
						acceptClassName="dropzone--accepted"
						rejectClassName="dropzone--rejected"
						multiple={false} // Only one video at the time
					>
						<p>Drop files here, or click to select manually</p>
					</Dropzone>
				)}
				{state === App.appStates.PROCESSING && (
					<BarLoader
						color={"rgb(54, 215, 183)"}
						className={css`
							margin: 0 auto;
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
