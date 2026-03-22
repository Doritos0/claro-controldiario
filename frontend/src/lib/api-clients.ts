import { AuthApi, Configuration as PythonConfiguration, WebApi } from "../api";
import { Configuration as NodeConfiguration, DefaultApi } from "../node";
import { getNodeAxios, getPythonAxios } from "./http";

const pythonBaseUrl = import.meta.env.VITE_API_PYTHON as string;
const nodeBaseUrl = import.meta.env.VITE_API_EXPRESS as string;

const pythonConfig = new PythonConfiguration({
  basePath: pythonBaseUrl,
});

const nodeConfig = new NodeConfiguration({
  basePath: nodeBaseUrl,
});

export function getAuthApi(): AuthApi {
  return new AuthApi(pythonConfig, pythonBaseUrl, getPythonAxios());
}

export function getWebApi(): WebApi {
  return new WebApi(pythonConfig, pythonBaseUrl, getPythonAxios());
}

export function getNodeApi(): DefaultApi {
  return new DefaultApi(nodeConfig, nodeBaseUrl, getNodeAxios());
}
