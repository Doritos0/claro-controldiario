# DefaultApi

All URIs are relative to *http://localhost:3000*

|Method | HTTP request | Description|
|------------- | ------------- | -------------|
|[**descargarFotos**](#descargarfotos) | **POST** /descargar | Descargar fotos de un grupo por fecha|

# **descargarFotos**
> descargarFotos(descargarFotosRequest)


### Example

```typescript
import {
    DefaultApi,
    Configuration,
    DescargarFotosRequest
} from './api';

const configuration = new Configuration();
const apiInstance = new DefaultApi(configuration);

let descargarFotosRequest: DescargarFotosRequest; //

const { status, data } = await apiInstance.descargarFotos(
    descargarFotosRequest
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **descargarFotosRequest** | **DescargarFotosRequest**|  | |


### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Proceso finalizado |  -  |
|**400** | Parámetros inválidos |  -  |
|**500** | Error en el servidor |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

