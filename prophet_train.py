import pickle
from fbprophet import Prophet
import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import datetime as dt
import argparse

class ProphetForecast:
    def __init__(self, train, test):
        self.train = train
        self.test = test

    def fit_model(self, n_predict):
        m = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=False)
        m.fit(self.train)
        future = m.make_future_dataframe(periods= len(self.test),freq= '1MIN')
        self.forecast = m.predict(future)

        return self.forecast

    def graph(self):
        fig = plt.figure(figsize=(40,10))
        # plt.plot(np.array(self.train["ds"]), np.array(self.train["y"]),'b', label="train", linewidth=3)
        # plt.plot(np.array(self.test["ds"]), np.array(self.test["y"]), 'g', label="test", linewidth=3)
        ds_forecast = np.array(self.forecast["ds"])
        forecast = np.array(self.forecast["yhat"])

        forecast_lower = np.array(self.forecast["yhat_lower"])
        forecast_upper = np.array(self.forecast["yhat_upper"])

        ds_forecast = ds_forecast[len(self.train["y"]):]
        forecast = forecast[len(self.train["y"]):]
        forecast_upper = forecast_upper[len(self.train["y"]):]
        forecast_lower = forecast_lower[len(self.train["y"]):]
        plt.plot(self.train["ds"], self.train["y"], 'b', label = 'train', linewidth = 3)
        plt.plot(self.test["ds"], self.test["y"], 'g', label = 'test', linewidth = 3)
        plt.plot(ds_forecast,forecast, 'y', label = 'yhat')
        forecast_ds = np.array(self.forecast["ds"])
        # plt.plot(forecast_ds, np.array(self.forecast["yhat"]), 'o', label="yhat", linewidth=3)
        plt.plot(ds_forecast, forecast_upper, 'y', label="yhat_upper", linewidth=3)
        plt.plot(ds_forecast, forecast_lower, 'y', label="yhat_lower", linewidth=3)
        plt.xlabel("Timestamp")
        plt.ylabel("Value")
        plt.legend(loc=1)
        plt.title("Prophet Model Forecast")

def calc_delta(vals):
    diff = vals - np.roll(vals, 1)
    diff[0] = 0
    return diff

def monotonically_inc(vals):
    # check corner case
    if len(vals) == 1:
        return True
    diff = calc_delta(vals)
    diff[np.where(vals == 0)] = 0

    if ((diff < 0).sum() == 0):
        return True
    else:
        return False

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="run Prophet training on time series")

    parser.add_argument("--metric", type=str, help='metric name', required=True)

    parser.add_argument("--key", type=int, help='key number')
    args = parser.parse_args()

    metric_name = args.metric
    # pkl_file = open("../pkl_data/" + metric_name + "_dataframes.pkl", "rb")
    pkl_file = open("../data/real_data_test.pkl", "rb")
    dfs = pickle.load(pkl_file)
    pkl_file.close()
    key_vals = list(dfs.keys())

    selected = [args.key]
    for ind in selected:
        key = key_vals[ind]
        df = dfs[key]
        #df = dfs["{'__name__': 'kubelet_docker_operations_latency_microseconds', 'beta_kubernetes_io_arch': 'amd64', 'beta_kubernetes_io_os': 'linux', 'instance': 'cpt-0001.ocp.prod.upshift.eng.rdu2.redhat.com', 'job': 'kubernetes-nodes', 'kubernetes_io_hostname': 'cpt-0001.ocp.prod.upshift.eng.rdu2.redhat.com', 'operation_type': 'version', 'provider': 'rhos', 'quantile': '0.5', 'region': 'compute', 'size': 'small'}"]
        df["ds"] = df["timestamps"]
        df["y"] = df["values"]
        df = df.sort_values(by=['ds'])
        print(key)
        df["y"] = df["y"].apply(pd.to_numeric)
        vals = np.array(df["y"].tolist())

        df["ds"] = df["ds"]
        df["y"] = df["y"]
        # check if metric is a counter, if so, run AD on difference
        if monotonically_inc(vals):
            print("monotonically_inc")
            vals = calc_delta(vals)
            df["y"] = vals.tolist()
        
        train = df[0:int(0.7*len(vals))]
        test = df[int(0.7*len(vals)):]

        pf = ProphetForecast(train, test)
        forecast = pf.fit_model(len(test))

        f = open("../prophet_forecasts/prophet_model_" + metric_name + "_" + str(args.key) + ".pkl", "wb")
        pickle.dump(forecast,f)
        print(type(forecast))
        pickle.dump(train, f)
        pickle.dump(test,f)
        f.close()
        
        pf.graph()
        plt.savefig("../presentation/graphs/prophet_" + str(args.key) + "_" + args.metric + ".png", transparent=True)



