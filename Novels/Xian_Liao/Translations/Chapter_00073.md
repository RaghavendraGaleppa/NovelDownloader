- 500: Internal Server Error
- 502: Bad Gateway
- 503: Service Unavailable
- 504: Gateway Timeout

### 3.3.3. 响应头

响应头（Response Headers）是 HTTP 响应中的一部分，它们提供了关于响应的附加信息，如响应的内容类型、编码方式、缓存策略等。响应头可以帮助客户端更好地处理服务器返回的内容。

#### 常见的响应头

1. **Content-Type**:
   - 描述：指示响应体的 MIME 类型。
   - 示例：`Content-Type: text/html; charset=UTF-8`

2. **Content-Length**:
   - 描述：响应体的长度（以字节为单位）。
   - 示例：`Content-Length: 348`

3. **Cache-Control**:
   - 描述：指定缓存机制。
   - 示例：`Cache-Control: no-cache`

4. **Set-Cookie**:
   - 描述：设置一个或多个 cookie。
   - 示例：`Set-Cookie: sessionid=38afes7a8; Path=/; HttpOnly`

5. **Location**:
   - 描述：用于重定向，指定新位置的 URL。
   - 示例：`Location: /new-page`

6. **Server**:
   - 描述：服务器的名称和版本。
   - 示例：`Server: Apache/2.4.1 (Unix)`

7. **Access-Control-Allow-Origin**:
   - 描述：用于 CORS（跨域资源共享），指定哪些源可以访问资源。
   - 示例：`Access-Control-Allow-Origin: *`

8. **Expires**:
   - 描述：响应过期的日期和时间。
   - 示例：`Expires: Thu, 01 Dec 2023 16:00:00 GMT`

9. **Last-Modified**:
   - 描述：资源的最后修改时间。
   - 示例：`Last-Modified: Tue, 15 Nov 2022 12:45:26 GMT`

10. **ETag**:
    - 描述：资源的特定版本的标识符，用于缓存验证。
    - 示例：`ETag: "737060cd8c284d8af7ad3082f209582d"`

#### 响应头的作用

- **内容协商**：如 `Content-Type` 告诉客户端如何解析响应体。
- **缓存控制**：如 `Cache-Control` 和 `Expires` 控制客户端如何缓存响应。
- **安全**：如 `Set-Cookie` 的 `HttpOnly` 和 `Secure` 标志增强安全性。
- **重定向**：如 `Location` 用于重定向到新的 URL。
- **跨域资源共享**：如 `Access-Control-Allow-Origin` 控制跨域请求。

#### 示例 HTTP 响应

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8
Content-Length: 138
Last-Modified: Mon, 10 Oct 2022 09:56:21 GMT
Server: Apache/2.4.1 (Unix)
Cache-Control: max-age=3600, must-revalidate
ETag: "5a8c-5b6d7e8f9a0b"
Date: Mon, 10 Oct 2022 10:00:00 GMT

<!DOCTYPE html>
<html>
<head>
    <title>Example</title>
</head>
<body>
    <p>Hello, World!</p>
</body>
</html>
```

### 3.3.4. 响应体

响应体（Response Body）是 HTTP 响应中的一部分，包含了服务器返回给客户端的实际数据。响应体的内容和格式由响应头中的 `Content-Type` 指定。

#### 响应体的内容

响应体的内容可以是各种格式，常见的包括：

1. **HTML**:
   - 用于网页。
   - 示例：
     ```html
     <!DOCTYPE html>
     <html>
     <head>
         <title>Example</title>
     </head>
     <body>
         <p>Hello, World!</p>
     </body>
     </html>
     ```

2. **JSON**:
   - 用于 API 响应。
   - 示例：
     ```json
     {
         "name": "John Doe",
         "age": 30,
         "city": "New York"
     }
     ```

3. **XML**:
   - 用于结构化数据。
   - 示例：
     ```xml
     <person>
         <name>John Doe</name>
         <age>30</age>
         <city>New York</city>
     </person>
     ```

4. **Plain Text**:
   - 纯文本。
   - 示例：
     ```
     Hello, World!
     ```

5. **Binary Data**:
   - 如图片、PDF 等。
   - 示例：图片的二进制数据。

#### 响应体的编码

响应体可以以不同的编码方式传输，常见的编码方式包括：

1. **Identity**:
   - 不压缩，直接传输。
   - 通过 `Content-Encoding: identity` 指定（通常省略）。

2. **Gzip**:
   - 使用 gzip 压缩。
   - 通过 `Content-Encoding: gzip` 指定。

3. **Deflate**:
   - 使用 zlib 压缩。
   - 通过 `Content-Encoding: deflate` 指定。

4. **Brotli**:
   - 使用 Brotli 压缩。
   - 通过 `Content-Encoding: br` 指定。

#### 示例 HTTP 响应

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=UTF-8
Content-Length: 56
Content-Encoding: gzip
Server: Apache/2.4.1 (Unix)
Date: Mon, 10 Oct 2022 10:00:00 GMT

<gzipped JSON data>
```

#### 响应体的重要性

- **数据传输**：响应体是服务器返回给客户端的主要数据载体。
- **内容格式**：通过 `Content-Type` 指定格式，客户端可以正确解析。
- **性能优化**：通过压缩（如 gzip）减少传输数据量，提高性能。

## 3.4. HTTP 方法

HTTP 方法（HTTP Methods）定义了客户端可以对服务器资源执行的操作。每种方法都有特定的语义和用途。

### 3.4.1. GET

GET 方法用于请求指定资源。GET 请求应该只用于获取数据，而不应该对资源的状态产生任何影响。

#### 特点

- **安全**：GET 请求是幂等的，多次执行相同的 GET 请求应该返回相同的结果。
- **可缓存**：GET 请求的响应可以被缓存。
- **长度限制**：GET 请求的参数通过 URL 传递，因此有长度限制（取决于浏览器和服务器）。

#### 示例

```http
GET /api/users?id=123 HTTP/1.1
Host: example.com
```

### 3.4.2. POST

POST 方法用于向指定资源提交数据，通常会导致服务器端的状态变化（如创建新资源）。

#### 特点

- **非幂等**：多次执行相同的 POST 请求可能会产生不同的结果（如创建多个资源）。
- **不可缓存**：POST 请求的响应通常不被缓存。
- **数据在请求体中**：POST 请求的数据放在请求体中，没有长度限制。

#### 示例

```http
POST /api/users HTTP/1.1
Host: example.com
Content-Type: application/json

{
    "name": "John Doe",
    "age": 30
}
```

### 3.4.3. PUT

PUT 方法用于替换指定资源的所有当前表示。如果资源不存在，PUT 可能会创建它。

#### 特点

- **幂等**：多次执行相同的 PUT 请求会产生相同的结果。
- **替换资源**：PUT 请求会替换整个资源，而不是部分更新。

#### 示例

```http
PUT /api/users/123 HTTP/1.1
Host: example.com
Content-Type: application/json

{
    "name": "John Doe",
    "age": 30
}
```

### 3.4.4. DELETE

DELETE 方法用于删除指定的资源。

#### 特点

- **幂等**：多次执行相同的 DELETE 请求会产生相同的结果（资源被删除后，后续删除请求可能返回 404）。
- **无请求体**：DELETE 请求通常没有请求体。

#### 示例

```http
DELETE /api/users/123 HTTP/1.1
Host: example.com
```

### 3.4.5. PATCH

PATCH 方法用于对资源进行部分修改。

#### 特点

- **非幂等**：多次执行相同的 PATCH 请求可能会产生不同的结果（取决于补丁的内容）。
- **部分更新**：PATCH 请求只更新资源的一部分，而不是整个资源。

#### 示例

```http
PATCH /api/users/123 HTTP/1.1
Host: example.com
Content-Type: application/json

{
    "age": 31
}
```

### 3.4.6. HEAD

HEAD 方法与 GET 方法类似，但服务器只返回响应头，不返回响应体。用于获取资源的元信息。

#### 特点

- **无响应体**：HEAD 请求的响应没有响应体。
- **可缓存**：HEAD 请求的响应头可以被缓存。

#### 示例

```http
HEAD /api/users/123 HTTP/1.1
Host: example.com
```

### 3.4.7. OPTIONS

OPTIONS 方法用于获取目标资源支持的通信选项（如支持的 HTTP 方法）。

#### 特点

- **预检请求**：常用于 CORS 预检请求。
- **返回支持的方法**：响应头 `Allow` 列出支持的 HTTP 方法。

#### 示例

```http
OPTIONS /api/users/123 HTTP/1.1
Host: example.com
```

### 3.4.8. TRACE

TRACE 方法用于回显服务器收到的请求，主要用于测试或诊断。

#### 特点

- **回显请求**：TRACE 请求的响应体包含原始请求的完整信息。
- **安全性**：可能暴露敏感信息，通常被禁用。

#### 示例

```http
TRACE /api/users/123 HTTP/1.1
Host: example.com
```

### 3.4.9. CONNECT

CONNECT 方法用于建立到目标资源的隧道（通常用于 HTTPS 代理）。

#### 特点

- **隧道**：CONNECT 请求用于建立网络隧道（如通过代理连接 HTTPS）。
- **代理使用**：主要用于 HTTP 代理。

#### 示例

```http
CONNECT example.com:443 HTTP/1.1
Host: example.com
```

## 3.5. HTTP 状态码

HTTP 状态码（HTTP Status Codes）是服务器对客户端请求的响应状态的三位数字代码。状态码分为五类：

### 3.5.1. 1xx（信息性状态码）

表示请求已被接收，需要继续处理。

- **100 Continue**：客户端应继续发送请求的剩余部分。
- **101 Switching Protocols**：服务器已理解客户端请求，并将通过 Upgrade 头字段切换协议。
- **102 Processing**：服务器已接收并正在处理请求，但尚无响应可用。
- **103 Early Hints**：用于在最终 HTTP 消息之前返回一些响应头。

### 3.5.2. 2xx（成功状态码）

表示请求已成功被服务器接收、理解并接受。

- **200 OK**：请求成功。GET 请求返回资源，POST 返回操作结果。
- **201 Created**：请求已被实现，且新资源已创建。
- **202 Accepted**：请求已被接受，但处理尚未完成。
- **203 Non-Authoritative Information**：返回的元信息来自缓存或副本。
- **204 No Content**：请求成功，但无内容返回。
- **205 Reset Content**：请求成功，客户端应重置文档视图。
- **206 Partial Content**：服务器已成功处理部分 GET 请求（用于范围请求）。
- **207 Multi-Status**：多状态响应，适用于 WebDAV。
- **208 Already Reported**：WebDAV，成员已在前面的请求中列举。
- **226 IM Used**：服务器已完成对资源的 GET 请求，响应是当前实例应用的一个或多个实例操作的结果。

### 3.5.3. 3xx（重定向状态码）

表示需要客户端采取进一步的操作才能完成请求。

- **300 Multiple Choices**：请求的资源有多个选择。
- **301 Moved Permanently**：资源已永久移动到新位置。
- **302 Found**：资源临时从不同的 URI 响应请求。
- **303 See Other**：对当前请求的响应可以在另一个 URI 上找到。
- **304 Not Modified**：资源未修改，可使用缓存版本。
- **305 Use Proxy**：请求的资源必须通过代理访问。
- **306 (Unused)**：原意是“后续请求应使用指定的代理”，现已弃用。
- **307 Temporary Redirect**：临时重定向，请求方法和主体不变。
- **308 Permanent Redirect**：永久重定向，请求方法和主体不变。

### 3.5.4. 4xx（客户端错误状态码）

表示客户端可能发生了错误，妨碍了服务器的处理。

- **400 Bad Request**：请求语法错误，服务器无法理解。
- **401 Unauthorized**：请求需要用户认证。
- **402 Payment Required**：保留，将来使用。
- **403 Forbidden**：服务器理解请求，但拒绝执行。
- **404 Not Found**：服务器未找到请求的资源。
- **405 Method Not Allowed**：请求方法不被目标资源支持。
- **406 Not Acceptable**：服务器无法生成客户端可接受的响应。
- **407 Proxy Authentication Required**：客户端需先通过代理认证。
- **408 Request Timeout**：服务器等待请求超时。
- **409 Conflict**：请求与资源的当前状态冲突。
- **410 Gone**：资源已永久删除。
- **411 Length Required**：请求需要定义 Content-Length。
- **412 Precondition Failed**：请求头中的前提条件失败。
- **413 Payload Too Large**：请求实体过大，服务器拒绝处理。
- **414 URI Too Long**：请求的 URI 过长，服务器拒绝处理。
- **415 Unsupported Media Type**：服务器不支持请求的媒体类型。
- **416 Range Not Satisfiable**：请求的范围无法满足。
- **417 Expectation Failed**：Expect 请求头无法满足。
- **418 I'm a teapot**：玩笑状态码，表示服务器是茶壶。
- **421 Misdirected Request**：请求被定向到无法生成响应的服务器。
- **422 Unprocessable Entity**：请求格式正确，但语义错误（WebDAV）。
- **423 Locked**：资源被锁定（WebDAV）。
- **424 Failed Dependency**：请求因之前的请求失败而失败（WebDAV）。
- **425 Too Early**：服务器不愿冒险处理可能重播的请求。
- **426 Upgrade Required**：客户端应切换到 TLS/1.0 等更高协议。
- **428 Precondition Required**：请求需要条件头。
- **429 Too Many Requests**：客户端发送了过多请求。
- **431 Request Header Fields Too Large**：请求头字段过大。
- **451 Unavailable For Legal Reasons**：因法律原因资源不可用。

### 3.5.5. 5xx（服务器错误状态码）

表示服务器在处理请求的过程中发生了错误。

- **500 Internal Server Error**：服务器内部错误，无法完成请求。
- **501 Not Implemented**：服务器不支持请求的功能。
- **502 Bad Gateway**：服务器作为网关或代理时，从上游服务器收到无效响应。
- **503 Service Unavailable**：服务器暂时过载或维护中。
- **504 Gateway Timeout**：服务器作为网关或代理时，未及时从上游服务器收到请求。
- **505 HTTP Version Not Supported**：服务器不支持请求的 HTTP 版本。
- **506 Variant Also Negotiates**：服务器存在内部配置错误。
- **507 Insufficient Storage**：服务器无法存储完成请求所需的内容（WebDAV）。
- **508 Loop Detected**：服务器在处理请求时检测到无限循环（WebDAV）。
- **510 Not Extended**：请求需要进一步扩展才能被服务器满足。
- **511 Network Authentication Required**：客户端需要进行身份验证才能获得网络访问权限。

## 3.6. HTTP 头部

HTTP 头部（HTTP Headers）是 HTTP 请求和响应中的元数据，用于传递额外的信息。头部可以分为请求头（Request Headers）、响应头（Response Headers）、实体头（Entity Headers）和通用头（General Headers）。

### 3.6.1. 通用头部

通用头部（General Headers）既可以出现在请求中，也可以出现在响应中。

- **Cache-Control**：指定缓存机制。
  - 示例：`Cache-Control: no-cache`
- **Connection**：控制本次连接是否保持。
  - 示例：`Connection: keep-alive`
- **Date**：消息发送的日期和时间。
  - 示例：`Date: Tue, 15 Nov 2022 08:12:31 GMT`
- **Pragma**：用于向后兼容 HTTP/1.0 缓存。
  - 示例：`Pragma: no-cache`
- **Trailer**：指示给定的头部字段在分块传输编码的消息尾部。
  - 示例：`Trailer: Expires`
- **Transfer-Encoding**：指定传输编码方式。
  - 示例：`Transfer-Encoding: chunked`
- **Upgrade**：升级到其他协议。
  - 示例：`Upgrade: HTTP/2.0`
- **Via**：代理服务器信息。
  - 示例：`Via: 1.0 fred, 1.1 example.com (Apache/1.1)`
- **Warning**：关于消息体的警告信息。
  - 示例：`Warning: 199 Miscellaneous warning`

### 3.6.2. 请求头部

请求头部（Request Headers）提供关于请求的附加信息。

- **Accept**：客户端可接受的响应内容类型。
  - 示例：`Accept: text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8`
- **Accept-Charset**：客户端可接受的字符集。
  - 示例：`Accept-Charset: utf-8, iso-8859-1;q=0.5`
- **Accept-Encoding**：客户端可接受的内容编码。
  - 示例：`Accept-Encoding: gzip, deflate`
- **Accept-Language**：客户端可接受的自然语言。
  - 示例：`Accept-Language: en-US, en;q=0.5`
- **Authorization**：认证信息。
  - 示例：`Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==`
- **Expect**：客户端期望的服务器行为。
  - 示例：`Expect: 100-continue`
- **From**：控制用户代理的用户电子邮件地址。
  - 示例：`From: user@example.com`
- **Host**：请求的目标主机和端口。
  - 示例：`Host: example.com:8080`
- **If-Match**：条件请求，仅当资源匹配给定 ETag 时才返回。
  - 示例：`If-Match: "737060cd8c284d8af7ad3082f209582d"`
- **If-Modified-Since**：条件请求，仅当资源在给定日期后修改过才返回。
  - 示例：`If-Modified-Since: Sat, 29 Oct 2022 19:43:31 GMT`
- **If-None-Match**：条件请求，仅当资源不匹配给定 ETag 时才返回。
  - 示例：`If-None-Match: "737060cd8c284d8af7ad3082f209582d"`
- **If-Range**：条件请求，如果资源未改变则返回范围请求的部分，否则返回整个资源。
  - 示例：`If-Range: "737060cd8c284d8af7ad3082f209582d"`
- **If-Unmodified-Since**：条件请求，仅当资源在给定日期后未修改过才返回。
  - 示例：`If-Unmodified-Since: Sat, 29 Oct 2022 19:43:31 GMT`
- **Max-Forwards**：限制代理或网关转发的次数。
  - 示例：`Max-Forwards: 10`
- **Proxy-Authorization**：向代理服务器认证。
  - 示例：`Proxy-Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==`
- **Range**：请求部分资源。
  - 示例：`Range: bytes=500-999`
- **Referer**：当前请求的来源页面。
  - 示例：`Referer: https://example.com/page.html`
- **TE**：客户端可接受的传输编码。
  - 示例：`TE: trailers, deflate;q=0.5`
- **User-Agent**：用户代理信息。
  - 示例：`User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36`

### 3.6.3. 响应头部

响应头部（Response Headers）提供关于响应的附加信息。

- **Accept-Ranges**：服务器是否接受范围请求。
  - 示例：`Accept-Ranges: bytes`
- **Age**：资源在代理缓存中存储的时间（秒）。
  - 示例：`Age: 12`
- **ETag**：资源的特定版本的标识符。
  - 示例：`ETag: "737060cd8c284d8af7ad3082f209582d"`
- **Location**：重定向目标。
  - 示例：`Location: /new-page`
- **Proxy-Authenticate**：代理服务器的认证信息。
  - 示例：`Proxy-Authenticate: Basic realm="Access to the internal site"`
- **Retry-After**：客户端应多久后重试。
  - 示例：`Retry-After: 120`
- **Server**：服务器信息。
  - 示例：`Server: Apache/2.4.1 (Unix)`
- **Vary**：决定缓存是否可用。
  - 示例：`Vary: User-Agent`
- **WWW-Authenticate**：服务器的认证信息。
  - 示例：`WWW-Authenticate: Basic realm="Access to the staging site"`

### 3.6.4. 实体头部

实体头部（Entity Headers）描述消息体的内容。

- **Allow**：资源支持的 HTTP 方法。
  - 示例：`Allow: GET, HEAD, PUT`
- **Content-Encoding**：内容编码方式。
  - 示例：`Content-Encoding: gzip`
- **Content-Language**：内容的自然语言。
  - 示例：`Content-Language: en`
- **Content-Length**：内容长度（字节）。
  - 示例：`Content-Length: 348`
- **Content-Location**：资源的替代位置。
  - 示例：`Content-Location: /index.html`
- **Content-MD5**：内容的 MD5 校验和。
  - 示例：`Content-MD5: Q2hlY2sgSW50ZWdyaXR5IQ==`
- **Content-Range**：部分内容的位置和总大小。
  - 示例：`Content-Range: bytes 21010-47021/47022`
- **Content-Type**：内容的 MIME 类型。
  - 示例：`Content-Type: text/html; charset=utf-8`
- **Expires**：内容的过期时间。
  - 示例：`Expires: Thu, 01 Dec 2022 16:00:00 GMT`
- **Last-Modified**：资源的最后修改时间。
  - 示例：`Last-Modified: Tue, 15 Nov 2022 12:45:26 GMT`

## 3.7. HTTP 缓存

HTTP 缓存（HTTP Caching）是通过存储资源的副本，减少重复请求和服务器负载的机制。缓存可以发生在客户端（浏览器缓存）或中间代理（代理缓存）。

### 3.7.1. 缓存控制

缓存控制（Cache Control）通过 HTTP 头部的 `Cache-Control` 和 `Expires` 等字段实现。

#### 缓存控制头

1. **Cache-Control**:
   - `max-age=<seconds>`：资源的最大缓存时间（秒）。
     - 示例：`Cache-Control: max-age=3600`
   - `no-cache`：缓存前必须向服务器验证。
     - 示例：`Cache-Control: no-cache`
   - `no-store`：禁止缓存。
     - 示例：`Cache-Control: no-store`
   - `public`：响应可被任何缓存存储。
     - 示例：`Cache-Control: public, max-age=3600`
   - `private`：响应只能被单个用户缓存（如浏览器）。
     - 示例：`Cache-Control: private, max-age=3600`
   - `must-revalidate`：缓存必须验证过期资源的有效性。
     - 示例：`Cache-Control: must-revalidate, max-age=3600`
   - `proxy-revalidate`：与 `must-revalidate` 类似，但仅适用于共享缓存。
     - 示例：`Cache-Control: proxy-revalidate, max-age=3600`
   - `s-maxage=<seconds>`：覆盖 `max-age`，仅适用于共享缓存。
     - 示例：`Cache-Control: s-maxage=3600`

2. **Expires**:
   - 指定资源的过期时间（HTTP/1.0）。
   - 示例：`Expires: Thu, 01 Dec 2022 16:00:00 GMT`

3. **Pragma**:
   - HTTP/1.0 的遗留字段，通常用于向后兼容。
   - 示例：`Pragma: no-cache`

#### 缓存验证

1. **Last-Modified** 和 **If-Modified-Since**:
   - 服务器通过 `Last-Modified` 返回资源的最后修改时间。
     - 示例：`Last-Modified: Tue, 15 Nov 2022 12:45:26 GMT`
   - 客户端通过 `If-Modified-Since` 发送缓存的最后修改时间，询问资源是否已修改。
     - 示例：`If-Modified-Since: Tue, 15 Nov 2022 12:45:26 GMT`
   - 如果资源未修改，服务器返回 `304 Not Modified`。

2. **ETag** 和 **If-None-Match**:
   - 服务器通过 `ETag` 返回资源的唯一标识符。
     - 示例：`ETag: "737060cd8c284d8af7ad3082f209582d"`
   - 客户端通过 `If-None-Match` 发送缓存的 ETag，询问资源是否已修改。
     - 示例：`If-None-Match: "737060cd8c284d8af7ad3082f209582d"`
   - 如果资源未修改，服务器返回 `304 Not Modified`。

### 3.7.2. 缓存策略

常见的缓存策略包括：

1. **强缓存**:
   - 通过 `Cache-Control` 和 `Expires` 实现。
   - 资源在有效期内直接从缓存读取，不发送请求到服务器。

2. **协商缓存**:
   - 通过 `Last-Modified` 和 `ETag` 实现。
   - 每次请求都发送到服务器验证资源是否已修改。

3. **混合缓存**:
   - 结合强缓存和协商缓存。
   - 先检查强缓存，过期后再验证协商缓存。

### 3.7.3. 缓存示例

#### 强缓存示例

```http
HTTP/1.1 200 OK
Cache-Control: public, max-age=3600
Content-Type: text/html
Content-Length: 1024

<!DOCTYPE html>
...
```

#### 协商缓存示例

```http
HTTP/1.1 200 OK
Cache-Control: no-cache
Last-Modified: Tue, 15 Nov 2022 12:45:26 GMT
ETag: "737060cd8c284d8af7ad3082f209582d"
Content-Type: text/html
Content-Length: 1024

<!DOCTYPE html>
...
```

#### 304 Not Modified 响应

```http
HTTP/1.1 304 Not Modified
Cache-Control: no-cache
Last-Modified: Tue, 15 Nov 2022 12:45:26 GMT
ETag: "737060cd8c284d8af7ad3082f209582d"
```

## 3.8. HTTP 安全

HTTP 安全（HTTP Security）涉及保护 HTTP 通信和数据的安全机制，包括身份验证、数据加密和防止攻击。

### 3.8.1. HTTPS

HTTPS（HTTP Secure）是 HTTP 的安全版本，通过 TLS/SSL 加密通信。

#### HTTPS 的特点

1. **加密**：使用 TLS/SSL 加密数据，防止窃听。
2. **认证**：通过证书验证服务器身份，防止中间人攻击。
3. **完整性**：防止数据在传输过程中被篡改。

#### HTTPS 的工作原理

1. 客户端发送 `ClientHello`，包含支持的加密算法和随机数。
2. 服务器响应 `ServerHello`，选择加密算法并发送证书和随机数。
3. 客户端验证证书，生成预主密钥并用服务器公钥加密后发送。
4. 服务器用私钥解密预主密钥，双方生成会话密钥。
5. 后续通信使用会话密钥加密。

#### 从 HTTP 切换到 HTTPS

1. **获取证书**：从 CA（如 Let's Encrypt）获取 SSL/TLS 证书。
2. **配置服务器**：在 Web 服务器（如 Nginx、Apache）中配置 HTTPS。
   - Nginx 示例：
     ```nginx
     server {
         listen 443 ssl;
         server_name example.com;
         ssl_certificate /path/to/cert.pem;
         ssl_certificate_key /path/to/key.pem;
         ...
     }
     ```
3. **重定向 HTTP 到 HTTPS**：
   - Nginx 示例：
     ```nginx
     server {
         listen 80;
         server_name example.com;
         return 301 https://$server_name$request_uri;
     }
     ```
4. **启用 HSTS**：通过 `Strict-Transport-Security` 头强制 HTTPS。
   - 示例：`Strict-Transport-Security: max-age=31536000; includeSubDomains`

### 3.8.2. CORS

跨域资源共享（Cross-Origin Resource Sharing, CORS）是一种机制，允许网页从不同域的服务器请求资源。

#### CORS 的工作原理

1. **简单请求**：
   - 满足以下条件：
     - 方法为 GET、HEAD 或 POST。
     - 头部为 `Accept`、`Accept-Language`、`Content-Language`、`Content-Type`（仅限 `application/x-www-form-urlencoded`、`multipart/form-data`、`text/plain`）。
   - 浏览器直接发送请求，并在响应中检查 `Access-Control-Allow-Origin`。

2. **预检请求**（Preflight Request）：
   - 不满足简单请求条件时，浏览器先发送 OPTIONS 请求。
   - 服务器响应是否允许实际请求。
   - 示例：
     ```http
     OPTIONS /resource HTTP/1.1
     Host: example.com
     Origin: https://example.org
     Access-Control-Request-Method: PUT
     Access-Control-Request-Headers: X-Custom-Header
     ```
     ```http
     HTTP/1.1 200 OK
     Access-Control-Allow-Origin: https://example.org
     Access-Control-Allow-Methods: PUT, POST, GET
     Access-Control-Allow-Headers: X-Custom-Header
     Access-Control-Max-Age: 86400
     ```

#### CORS 头部

1. **请求头**：
   - `Origin`：请求的来源。
     - 示例：`Origin: https://example.com`
   - `Access-Control-Request-Method`：预检请求中声明实际请求的方法。
     - 示例：`Access-Control-Request-Method: POST`
   - `Access-Control-Request-Headers`：预检请求中声明实际请求的头部。
     - 示例：`Access-Control-Request-Headers: X-Custom-Header`

2. **响应头**：
   - `Access-Control-Allow-Origin`：允许的来源（或 `*`）。
     - 示例：`Access-Control-Allow-Origin: https://example.com`
   - `Access-Control-Allow-Methods`：允许的方法。
     - 示例：`Access-Control-Allow-Methods: GET, POST, PUT`
   - `Access-Control-Allow-Headers`：允许的头部。
     - 示例：`Access-Control-Allow-Headers: X-Custom-Header`
   - `Access-Control-Allow-Credentials`：是否允许发送凭据（如 cookies）。
     - 示例：`Access-Control-Allow-Credentials: true`
   - `Access-Control-Expose-Headers`：允许客户端访问的响应头。
     - 示例：`Access-Control-Expose-Headers: X-Custom-Header`
   - `Access-Control-Max-Age`：预检请求的缓存时间（秒）。
     - 示例：`Access-Control-Max-Age: 86400`

#### CORS 示例

1. 允许所有来源：
   ```http
   Access-Control-Allow-Origin: *
   ```

2. 允许特定来源并支持凭据：
   ```http
   Access-Control-Allow-Origin: https://example.com
   Access-Control-Allow-Credentials: true
   ```

3. 复杂请求的预检和响应：
   - 预检请求：
     ```http
     OPTIONS /data HTTP/1.1
     Host: api.example.com
     Origin: https://example.com
     Access-Control-Request-Method: PUT
     Access-Control-Request-Headers: X-Custom-Header
     ```
   - 预检响应：
     ```http
     HTTP/1.1 200 OK
     Access-Control-Allow-Origin: https://example.com
     Access-Control-Allow-Methods: PUT, GET, POST, OPTIONS
     Access-Control-Allow-Headers: X-Custom-Header
     Access-Control-Max-Age: 86400
     ```
   - 实际请求：
     ```http
     PUT /data HTTP/1.1
     Host: api.example.com
     Origin: https://example.com
     X-Custom-Header: value
     ```
   - 实际响应：
     ```http
     HTTP/1.1 200 OK
     Access-Control-Allow-Origin: https://example.com
     Content-Type: application/json

     {"status": "success"}
     ```

### 3.8.3. CSRF

跨站请求伪造（Cross-Site Request Forgery, CSRF）是一种攻击方式，攻击者诱使用户在已认证的 Web 应用中执行非预期的操作。

#### CSRF 防护措施

1. **CSRF Token**：
   - 服务器生成随机 Token 并嵌入表单或请求头。
   - 提交请求时验证 Token。
   - 示例：
     ```html
     <form action="/transfer" method="POST">
         <input type="hidden" name="csrf_token" value="random_token_123">
         <input type="text" name="amount">
         <input type="submit" value="Transfer">
     </form>
     ```

2. **SameSite Cookie**：
   - 设置 `SameSite` 属性限制 Cookie 的跨站发送。
   - 选项：
     - `Strict`：仅同站发送。
     - `Lax`：同站和顶级导航发送（默认）。
     - `None`：允许跨站发送（需配合 `Secure`）。
   - 示例：
     ```http
     Set-Cookie: sessionid=38afes7a8; Path=/; SameSite=Lax
     ```

3. **验证 Origin/Referer 头**：
   - 检查 `Origin` 或 `Referer` 头是否来自可信来源。
   - 示例（Nginx）：
     ```nginx
     if ($http_origin !~* "^https://example.com$") {
         return 403;
     }
     ```

#### CSRF 示例

1. 攻击场景：
   - 用户登录银行网站（`bank.com`），会话 Cookie 有效。
   - 用户访问恶意网站，其中包含：
     ```html
     <form action="https://bank.com/transfer" method="POST">
         <input type="hidden" name="amount" value="1000">
         <input type="hidden" name="to" value="attacker">
     </form>
     <script>document.forms[0].submit();</script>
     ```
   - 浏览器自动发送 Cookie，完成转账。

2. 防护后的请求：
   - 表单包含 CSRF Token：
     ```html
     <form action="/transfer" method="POST">
         <input type="hidden" name="csrf_token" value="random_token_123">
         <input type="text" name="amount">
         <input type="submit" value="Transfer">
     </form>
     ```
   - 服务器验证 Token：
     ```python
     if request.form['csrf_token'] != session['csrf_token']:
         abort(403)
     ```

### 3.8.4. XSS

跨站脚本（Cross-Site Scripting, XSS）是一种攻击方式，攻击者向网页注入恶意脚本，在用户浏览器中执行。

#### XSS 类型

1. **存储型 XSS**：
   - 恶意脚本存储在服务器（如评论、论坛帖子）。
   - 用户访问受影响页面时执行。

2. **反射型 XSS**：
   - 恶意脚本作为请求参数（如 URL）的一部分。
   - 服务器返回包含脚本的响应。

3. **DOM 型 XSS**：
   - 恶意脚本通过修改 DOM 环境在客户端执行。
   - 不涉及服务器响应。

#### XSS 防护措施

1. **输入验证和过滤**：
   - 对用户输入进行验证和过滤（如移除 `<script>` 标签）。
   - 示例（Python）：
     ```python
     from bleach import clean
     cleaned_input = clean(user_input, tags=[], attributes={}, styles=[], strip=True)
     ```

2. **输出编码**：
   - 在输出到 HTML 前进行编码。
   - 示例（JavaScript）：
     ```javascript
     function escapeHtml(text) {
         return text.replace(/&/g, "&amp;")
                   .replace(/</g, "&lt;")
                   .replace(/>/g, "&gt;")
                   .replace(/"/g, "&quot;")
                   .replace(/'/g, "&#039;");
     }
     ```

3. **Content Security Policy (CSP)**：
   - 通过 HTTP 头限制可执行的脚本来源。
   - 示例：
     ```http
     Content-Security-Policy: default-src 'self'; script-src 'self' https://trusted.cdn.com
     ```

4. **HttpOnly Cookie**：
   - 设置 `HttpOnly` 防止 JavaScript 访问 Cookie。
   - 示例：
     ```http
     Set-Cookie: sessionid=38afes7a8; Path=/; HttpOnly
     ```

#### XSS 示例

1. 攻击场景：
   - 恶意用户提交评论：
     ```html
     <script>alert('XSS');</script>
     ```
   - 未过滤的页面显示评论时执行脚本。

2. 防护后的输出：
   - 评论内容被编码：
     ```html
     &lt;script&gt;alert(&#039;XSS&#039;);&lt;/script&gt;
     ```
   - 或通过 CSP 阻止内联脚本执行。

### 3.8.5. 其他安全头部

通过设置 HTTP 响应头增强安全性：

1. **Strict-Transport-Security (HSTS)**：
   - 强制使用 HTTPS。
   - 示例：`Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`

2. **X-Content-Type-Options**：
   - 防止 MIME 类型嗅探。
   - 示例：`X-Content-Type-Options: nosniff`

3. **X-Frame-Options**：
   - 防止点击劫持。
   - 示例：`X-Frame-Options: DENY`

4. **X-XSS-Protection**：
   - 启用浏览器 XSS 过滤器。
   - 示例：`X-XSS-Protection: 1; mode=block`

5. **Referrer-Policy**：
   - 控制 Referer 头的发送。
   - 示例：`Referrer-Policy: no-referrer-when-downgrade`

6. **Feature-Policy**：
   - 控制浏览器特性的使用。
   - 示例：`Feature-Policy: geolocation 'self' https://example.com`

#### 完整的安全头部示例

```http
HTTP/1.1 200 OK
Content-Type: text/html
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'; script-src 'self' https://trusted.cdn.com
Referrer-Policy: no-referrer-when-downgrade
Feature-Policy: geolocation 'self'

<!DOCTYPE html>
...
```

## 3.9. HTTP/2

HTTP/2 是 HTTP 协议的第二个主要版本，旨在提高性能和效率。

### 3.9.1. 二进制分帧

HTTP/2 将通信分解为二进制帧，替代 HTTP/1.x 的文本格式。

#### 帧类型

1. **HEADERS**：包含 HTTP 头部。
2. **DATA**：包含消息体。
3. **PRIORITY**：指定流的优先级。
4. **RST_STREAM**：终止流。
5. **SETTINGS**：配置连接参数。
6. **PUSH_PROMISE**：服务器推送资源。
7. **PING**：测试连接和延迟。
8. **GOAWAY**：停止创建流的通知。
9. **WINDOW_UPDATE**：流量控制。
10. **CONTINUATION**：延续 HEADERS 帧。

#### 示例

- HTTP/1.1 请求：
  ```http
  GET /index.html HTTP/1.1
  Host: example.com
  ```
- HTTP/2 等效：
  - HEADERS 帧（流 ID=1，包含 :method=GET, :path=/index.html, :authority=example.com）
  - 可能跟随 DATA 帧（如果请求有体）

### 3.9.2. 多路复用

HTTP/2 通过流（Stream）支持多路复用，允许在单一连接上并行交错多个请求和响应。

#### 流的特点

1. **标识符**：每个流有唯一的 31 位整数 ID。
2. **双向性**：客户端和服务器可以独立发送帧。
3. **优先级**：流可以分配优先级权重和依赖关系。
4. **流量控制**：每个流可以独立控制流量。

#### 多路复用 vs HTTP/1.x

- HTTP/1.x：
  - 并行请求需要多个 TCP 连接（受浏览器限制，通常 6-8 个）。
  - 队头阻塞：慢请求阻塞后续请求。
- HTTP/2：
  - 单一连接上并行处理多个流。
  - 帧交错避免队头阻塞。

### 3.9.3. 头部压缩

HTTP/2 使用 HPACK 压缩算法减少头部大小。

#### HPACK 的特点

1. **静态表**：包含 61 个常见头部字段和值。
2. **动态表**：在连接中动态更新的头部字段。
3. **哈夫曼编码**：对字符串进行压缩。

#### 示例

- HTTP/1.1 头部：
  ```http
  GET /index.html HTTP/1.1
  Host: example.com
  User-Agent: Mozilla/5.0
  Accept: text/html
  ```
- HTTP/2 编码：
  - 静态表索引：:method=GET (2), :path=/index.html (4), :authority=example.com (1)
  - 动态表添加：user-agent (索引 62), accept (索引 63)
  - 后续请求可以引用这些索引。

### 3.9.4. 服务器推送

服务器推送（Server Push）允许服务器主动发送资源给客户端，无需客户端明确请求。

#### 推送流程

1. 客户端请求 `/index.html`。
2. 服务器响应 `/index.html` 并推送 `/style.css` 和 `/script.js`。
3. 客户端缓存推送的资源，后续需要时直接使用。

#### 推送示例

- 服务器发送 PUSH_PROMISE 帧：
  ```http2
  PUSH_PROMISE (stream_id=1)
  :method: GET
  :path: /style.css
  :authority: example.com
  ```
- 然后发送 HEADERS 和 DATA 帧包含 `/style.css` 的内容。

#### 推送的合理使用

1. **缓存策略**：推送的资源应有适当的缓存控制。
2. **避免过度推送**：只推送高概率使用的资源。
3. **客户端取消**：客户端可以通过 RST_STREAM 拒绝推送。

### 3.9.5. 流量控制

HTTP/2 提供基于流的流量控制，防止发送方压倒接收方。

#### 流量控制机制

1. **窗口大小**：每个流和整个连接有信用窗口。
2. **WINDOW_UPDATE**：接收方发送此帧增加窗口大小。
3. **初始窗口**：默认 65,535 字节。

#### 示例

1. 客户端设置初始窗口为 10,000 字节。
2. 服务器发送 10,000 字节后暂停。
3. 客户端处理数据后发送 WINDOW_UPDATE 增加窗口。
4. 服务器继续发送数据。

### 3.9.6. HTTP/2 与 HTTPS

虽然 HTTP/2 标准不强制加密，但主流浏览器只支持 HTTP/2 over TLS（h2）。

#### ALPN

应用层协议协商（Application-Layer Protocol Negotiation, ALPN）用于 TLS 握手时协商 HTTP/2。

1. 客户端在 ClientHello 中列出支持的协议（如 h2, http/1.1）。
2. 服务器在 ServerHello 中选择协议（如 h2）。
3. 后续通信使用 HTTP/2。

### 3.9.7. 升级到 HTTP/2

#### 从 HTTP/1.1 升级

1. 客户端发送：
   ```http
   GET / HTTP/1.1
   Host: example.com
   Connection: Upgrade, HTTP2-Settings
   Upgrade: h2c
   HTTP2-Settings: <base64url SETTINGS payload>
   ```
2. 服务器同意升级：
   ```http
   HTTP/1.1 101 Switching Protocols
   Connection: Upgrade
   Upgrade: h2c
   ```
3. 后续通信使用 HTTP/2。

#### 直接 HTTP/2

- 通过 ALPN 在 TLS 握手时协商。
- 或直接建立 h2c（非加密 HTTP/2）连接。

### 3.9.8. HTTP/2 的局限性

1. **TCP 层队头阻塞**：单个丢包会影响所有流。
2. **服务器推送的采用率低**：难以准确预测客户端需求。
3. **设置复杂性**：需要正确配置 TLS 和服务器参数。

## 3.10. HTTP/3

HTTP/3 是 HTTP 协议的第三个主要版本，基于 QUIC 协议，旨在进一步改进性能和安全性。

### 3.10.1. QUIC 协议

QUIC（Quick UDP Internet Connections）是 Google 开发的基于 UDP 的传输协议，现被 IETF 标准化为 HTTP/3 的基础。

#### QUIC 的特点

1. **基于 UDP**：绕过 TCP 的限制，避免操作系统内核的依赖。
2. **内置加密**：默认使用 TLS 1.3。
3. **连接迁移**：使用连接 ID 而非 IP/端口，支持网络切换。
4. **多路复用**：类似 HTTP/2，但解决了队头阻塞问题。
5. **快速握手**：0-RTT 和 1-RTT 连接建立。

#### QUIC vs TCP

| 特性                | QUIC                      | TCP                |
|---------------------|---------------------------|--------------------|
| 传输层              | UDP                       | TCP                |
| 加密                | 内置 (TLS 1.3)            | 可选 (TLS)         |
| 队头阻塞            | 无 (每个流独立)           | 有                 |
| 握手延迟            | 0-RTT 或 1-RTT            | 1-RTT (TLS 1.3)    |
| 连接迁移            | 支持                      | 不支持             |

### 3.10.2. HTTP/3 的特点

1. **流多路复用**：独立流避免队头阻塞。
2. **改进的拥塞控制**：更灵活的算法实现。
3. **前向纠错 (FEC)**：减少重传延迟。
4. **无缝连接迁移**：设备切换网络时保持连接。

### 3.10.3. HTTP/3 部署

#### 服务器配置

1. **监听 UDP 端口**：通常与 HTTPS 相同的 443 端口。
2. **Alt-Svc 头**：通过 HTTP/2 或 HTTP/1.1 告知客户端支持 HTTP/3。
   - 示例：`Alt-Svc: h3=":443"; ma=86400`
3. **DNS 记录**：通过 HTTPS RR 或 SVCB 记录指示 HTTP/3 支持。

#### 客户端支持

- 现代浏览器（Chrome, Firefox, Edge, Safari）支持 HTTP/3。
- 需要显式启用或默认支持。

### 3.10.4. HTTP/3 示例

#### 连接建立

1. 客户端发送 QUIC Initial 包（包含 TLS 1.3 握手）。
2. 服务器响应，完成 1-RTT 握手（或 0-RTT 恢复会话）。
3. 建立 HTTP/3 连接。

#### 请求/响应

- 类似 HTTP/2，但帧通过 QUIC 流传输：
  - 客户端打开控制流和请求流。
  - 服务器通过单向流推送资源。

### 3.10.5. 升级到 HTTP/3

#### 渐进式升级

1. 保持 HTTP/1.1 和 HTTP/2 支持。
2. 通过 Alt-Svc 头通告 HTTP/3 支持。
3. 客户端尝试升级，失败时回退。

#### 配置示例

- Nginx (通过 Cloudflare 或自定义补丁)：
  ```nginx
  listen 443 quic reuseport;
  listen 443 ssl;
  ssl_protocols TLSv1.3;
  add_header Alt-Svc 'h3=":443"; ma=86400';
  ```

### 3.10.6. HTTP/3 的挑战

1. **中间设备支持**：某些网络设备可能阻止 UDP 或 QUIC。
2. **CPU 开销**：加密和 QUIC 处理比 TCP 更耗资源。
3. **部署复杂性**：需要同时维护多个协议版本。