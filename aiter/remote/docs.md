This library makes it easy to create typed RPCs while being agnostic about details such as transport and marshaling.

Features include easy multiplexing, symmetric connections (so it's easy to create both peer-to-peer RPCs and client/server), and expandability of 

Example potential transports include TCP, UDP, HTTP, or serial.

Example marshalings include simple JSON, BSON, CBOR, text, or custom binary.

After a connection is established, one or more remote object's APIs are exposed, corresponding to integer channels. Remote API objects are represented locally by a `Proxy` object, which captures invocations, turns them into tuples of messages, and passes them to the `RPCStream` object.

Python type hints are extracted, allowing for arbitrarily complex objects to be sent, and call user code the serialize the invocation using any method that doesn't lose information, and the message is sent over the wire.

On the other side, the messages are reconstructed, and the type hints are used to reverse the serialization. The intended recipient of the message is located, and the appropriate async method is invoked, returning some value. The return value (or error) is serialized and sent remotely using the exact same mechanism as above, where is sets the target (a `Future`) to `done`.

An `RPCStream` object can be used to make one or more objects (called "APIs") available remotely by exposing their async methods as RPC calls.

