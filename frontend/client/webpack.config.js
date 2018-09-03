const webpack = require("webpack");
const merge = require("webpack-merge");
const UglifyJsPlugin = require("uglifyjs-webpack-plugin");

let common = {
    entry: {
        app: __dirname + "/App.js"
    },
    output: {
        path: __dirname + "/../static/frontend/js",
        filename: "[name].client.js"
    },
    externals: {
        cheerio: "window",
        "react/lib/ExecutionEnvironment": true,
        "react/lib/ReactContext": true
    },
    module: {
        rules: [
            {
                test: /\.jsx?$/,
                exclude: /(node_modules|bower_components)/,
                loader: "babel-loader",
                query: {
                    presets: ["react", "stage-0", "flow"],
                    plugins: ["emotion"]
                }
            },
            {
                test: /\.css$/,
                use: ["style-loader", "css-loader"]
            }
        ]
    }
};

if (process.env.NODE_ENV === "production") {
    module.exports = merge(common, {
        plugins: [
            new webpack.DefinePlugin({
                "process.env.NODE_ENV": JSON.stringify("production")
            }),
            new UglifyJsPlugin()
        ],
        mode: "production"
    });
} else {
    module.exports = merge(common, {
        mode: "development"
    });
}
