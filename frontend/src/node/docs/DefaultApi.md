# DefaultApi

All URIs are relative to *http://localhost:3000*

|Method | HTTP request | Description|
|------------- | ------------- | -------------|
|[**descargarFotos**](#descargarfotos) | **POST** /descargar | Descargar fotos de un grupo por fecha|
|[**iniciarSesionWhatsapp**](#iniciarsesionwhatsapp) | **POST** /iniciar-sesion | Inicializa la sesión de WhatsApp y devuelve estado + QR|
|[**listarGruposWhatsapp**](#listargruposwhatsapp) | **GET** /grupos | Lista los grupos disponibles de la sesión autenticada|
|[**obtenerEstadoSesionWhatsapp**](#obtenerestadosesionwhatsapp) | **GET** /estado-sesion | Devuelve el estado actual de la sesión de WhatsApp|

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
|**503** | WhatsApp no está listo |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **iniciarSesionWhatsapp**
> SessionState iniciarSesionWhatsapp()


### Example

```typescript
import {
    DefaultApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new DefaultApi(configuration);

const { status, data } = await apiInstance.iniciarSesionWhatsapp();
```

### Parameters
This endpoint does not have any parameters.


### Return type

**SessionState**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Estado de sesión de WhatsApp |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **listarGruposWhatsapp**
> Array<GroupInfo> listarGruposWhatsapp()


### Example

```typescript
import {
    DefaultApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new DefaultApi(configuration);

const { status, data } = await apiInstance.listarGruposWhatsapp();
```

### Parameters
This endpoint does not have any parameters.


### Return type

**Array<GroupInfo>**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Lista de grupos |  -  |
|**503** | WhatsApp no está listo |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **obtenerEstadoSesionWhatsapp**
> SessionState obtenerEstadoSesionWhatsapp()


### Example

```typescript
import {
    DefaultApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new DefaultApi(configuration);

const { status, data } = await apiInstance.obtenerEstadoSesionWhatsapp();
```

### Parameters
This endpoint does not have any parameters.


### Return type

**SessionState**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Estado actual |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

