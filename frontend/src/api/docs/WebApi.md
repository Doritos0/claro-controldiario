# WebApi

All URIs are relative to *http://localhost:8000/api*

|Method | HTTP request | Description|
|------------- | ------------- | -------------|
|[**agregarConfiguracion**](#agregarconfiguracion) | **POST** /post_configuracion | Post Configracion|
|[**agregarConfiguracion_0**](#agregarconfiguracion_0) | **POST** /post_configuracion | Post Configracion|
|[**crearEjecutivo**](#crearejecutivo) | **POST** /ejecutivos | Crear Ejecutivo|
|[**crearEjecutivo_0**](#crearejecutivo_0) | **POST** /ejecutivos | Crear Ejecutivo|
|[**ejecutarReporteDiario**](#ejecutarreportediario) | **POST** /ejecutar | Ejecutar|
|[**ejecutarReporteDiario_0**](#ejecutarreportediario_0) | **POST** /ejecutar | Ejecutar|
|[**obtenerConfiguracion**](#obtenerconfiguracion) | **POST** /get_configuracion | Get Configuracion|
|[**obtenerConfiguracion_0**](#obtenerconfiguracion_0) | **POST** /get_configuracion | Get Configuracion|
|[**peticionTest**](#peticiontest) | **GET** /test | Test|
|[**registrarUsuario**](#registrarusuario) | **POST** /usuarios | Registrar Usuario|
|[**registrarUsuario_0**](#registrarusuario_0) | **POST** /usuarios | Registrar Usuario|

# **agregarConfiguracion**
> Configuracion agregarConfiguracion(postConfiguracionRequest)


### Example

```typescript
import {
    WebApi,
    Configuration,
    PostConfiguracionRequest
} from './api';

const configuration = new Configuration();
const apiInstance = new WebApi(configuration);

let postConfiguracionRequest: PostConfiguracionRequest; //

const { status, data } = await apiInstance.agregarConfiguracion(
    postConfiguracionRequest
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **postConfiguracionRequest** | **PostConfiguracionRequest**|  | |


### Return type

**Configuracion**

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **agregarConfiguracion_0**
> Configuracion agregarConfiguracion_0(postConfiguracionRequest)


### Example

```typescript
import {
    WebApi,
    Configuration,
    PostConfiguracionRequest
} from './api';

const configuration = new Configuration();
const apiInstance = new WebApi(configuration);

let postConfiguracionRequest: PostConfiguracionRequest; //

const { status, data } = await apiInstance.agregarConfiguracion_0(
    postConfiguracionRequest
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **postConfiguracionRequest** | **PostConfiguracionRequest**|  | |


### Return type

**Configuracion**

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **crearEjecutivo**
> number crearEjecutivo(ejecutivoRest)


### Example

```typescript
import {
    WebApi,
    Configuration,
    EjecutivoRest
} from './api';

const configuration = new Configuration();
const apiInstance = new WebApi(configuration);

let ejecutivoRest: EjecutivoRest; //

const { status, data } = await apiInstance.crearEjecutivo(
    ejecutivoRest
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **ejecutivoRest** | **EjecutivoRest**|  | |


### Return type

**number**

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **crearEjecutivo_0**
> number crearEjecutivo_0(ejecutivoRest)


### Example

```typescript
import {
    WebApi,
    Configuration,
    EjecutivoRest
} from './api';

const configuration = new Configuration();
const apiInstance = new WebApi(configuration);

let ejecutivoRest: EjecutivoRest; //

const { status, data } = await apiInstance.crearEjecutivo_0(
    ejecutivoRest
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **ejecutivoRest** | **EjecutivoRest**|  | |


### Return type

**number**

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **ejecutarReporteDiario**
> any ejecutarReporteDiario(ejecutarRequest)


### Example

```typescript
import {
    WebApi,
    Configuration,
    EjecutarRequest
} from './api';

const configuration = new Configuration();
const apiInstance = new WebApi(configuration);

let ejecutarRequest: EjecutarRequest; //

const { status, data } = await apiInstance.ejecutarReporteDiario(
    ejecutarRequest
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **ejecutarRequest** | **EjecutarRequest**|  | |


### Return type

**any**

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **ejecutarReporteDiario_0**
> any ejecutarReporteDiario_0(ejecutarRequest)


### Example

```typescript
import {
    WebApi,
    Configuration,
    EjecutarRequest
} from './api';

const configuration = new Configuration();
const apiInstance = new WebApi(configuration);

let ejecutarRequest: EjecutarRequest; //

const { status, data } = await apiInstance.ejecutarReporteDiario_0(
    ejecutarRequest
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **ejecutarRequest** | **EjecutarRequest**|  | |


### Return type

**any**

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **obtenerConfiguracion**
> Configuracion obtenerConfiguracion()


### Example

```typescript
import {
    WebApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new WebApi(configuration);

const { status, data } = await apiInstance.obtenerConfiguracion();
```

### Parameters
This endpoint does not have any parameters.


### Return type

**Configuracion**

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **obtenerConfiguracion_0**
> Configuracion obtenerConfiguracion_0()


### Example

```typescript
import {
    WebApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new WebApi(configuration);

const { status, data } = await apiInstance.obtenerConfiguracion_0();
```

### Parameters
This endpoint does not have any parameters.


### Return type

**Configuracion**

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **peticionTest**
> string peticionTest()


### Example

```typescript
import {
    WebApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new WebApi(configuration);

const { status, data } = await apiInstance.peticionTest();
```

### Parameters
This endpoint does not have any parameters.


### Return type

**string**

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **registrarUsuario**
> RegisterResponse registrarUsuario(registerRequest)


### Example

```typescript
import {
    WebApi,
    Configuration,
    RegisterRequest
} from './api';

const configuration = new Configuration();
const apiInstance = new WebApi(configuration);

let registerRequest: RegisterRequest; //

const { status, data } = await apiInstance.registrarUsuario(
    registerRequest
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **registerRequest** | **RegisterRequest**|  | |


### Return type

**RegisterResponse**

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **registrarUsuario_0**
> RegisterResponse registrarUsuario_0(registerRequest)


### Example

```typescript
import {
    WebApi,
    Configuration,
    RegisterRequest
} from './api';

const configuration = new Configuration();
const apiInstance = new WebApi(configuration);

let registerRequest: RegisterRequest; //

const { status, data } = await apiInstance.registrarUsuario_0(
    registerRequest
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **registerRequest** | **RegisterRequest**|  | |


### Return type

**RegisterResponse**

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

