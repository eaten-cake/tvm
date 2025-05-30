# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import pickle
import random

import numpy as np

import tvm
import tvm.testing
from tvm import nd
from tvm.runtime import container as _container


def test_string():
    s = tvm.runtime.String("xyz")

    assert isinstance(s, str)
    assert s.startswith("xy")
    assert s + "1" == "xyz1"
    y = tvm.testing.echo(s)
    assert isinstance(y, str)
    assert s == y

    x = tvm.ir.load_json(tvm.ir.save_json(y))
    assert x == y

    # test pickle
    z = pickle.loads(pickle.dumps(s))
    assert s == z


def test_shape_tuple():
    shape = [random.randint(-10, 10) for _ in range(5)]
    stuple = _container.ShapeTuple(shape)
    len(stuple) == len(shape)
    for a, b in zip(stuple, shape):
        assert a == b
    # ShapleTuple vs. tuple
    assert stuple == tuple(shape)
    # ShapleTuple vs. ShapeTuple
    assert stuple == _container.ShapeTuple(shape)

    # test pickle
    z = pickle.loads(pickle.dumps(stuple))
    assert isinstance(z, tvm.runtime.ShapeTuple)
    assert stuple == z


def test_bool_argument():
    """Boolean objects are currently stored as int"""
    func = tvm.get_global_func("testing.AcceptsBool")

    assert isinstance(func(True), bool)
    assert isinstance(func(1), bool)
    assert isinstance(func(0), bool)


def test_int_argument():
    func = tvm.get_global_func("testing.AcceptsInt")

    assert isinstance(func(True), int)
    assert isinstance(func(1), int)
    assert isinstance(func(0), int)


def test_object_ref_array_argument():
    func = tvm.get_global_func("testing.AcceptsObjectRefArray")

    assert isinstance(func([True, 17, "hello"]), bool)
    assert isinstance(func([True]), bool)
    assert isinstance(func([17]), int)
    assert isinstance(func(["hello"]), str)


def test_map_argument_returns_value():
    func = tvm.get_global_func("testing.AcceptsMapReturnsValue")

    res = func({"a": 1, "b": 2}, "a")
    assert isinstance(res, int)
    assert res == 1

    res = func({"a": True, "b": False}, "a")
    assert isinstance(res, bool)
    assert res == True


def test_map_argument_returns_map():
    func = tvm.get_global_func("testing.AcceptsMapReturnsMap")

    res = func({"a": 1, "b": 2})
    for key, value in res.items():
        assert isinstance(key, str)
        assert isinstance(value, int)

    res = func({"a": False, "b": True})
    for key, value in res.items():
        assert isinstance(key, str)
        assert isinstance(value, bool)


def test_conversion_of_arg():
    """Arguments may be converted

    The calling side of the FFI converts to types that are available
    at runtime.  However, there may be additional type conversions
    required, that must be performed on the callee-side of the FFI.
    """

    func = tvm.get_global_func("testing.AcceptsPrimExpr")

    res = func(1)
    assert isinstance(res, tvm.tir.IntImm)
    assert res.dtype == "int32"

    res = func(True)
    assert isinstance(res, tvm.tir.IntImm)
    assert res.dtype == "bool"


def test_conversion_of_array_elements():
    """Elements of an array may require conversion from FFI to param type

    Like `test_conversion_of_arg`, but conversions must be applied
    recursively to array elements.  Here, the Python-side of the FFI
    converts the array `[1,2]` to `Array{runtime::Int(1),
    runtime::Int(2)}`, and the C++ side of the FFI converts to
    `Array{IntImm(1), IntImm(2)}`.
    """

    func = tvm.get_global_func("testing.AcceptsArrayOfPrimExpr")

    res = func([1, False])
    assert isinstance(res[0], tvm.tir.IntImm)
    assert res[0].dtype == "int32"
    assert isinstance(res[1], tvm.tir.IntImm)
    assert res[1].dtype == "bool"


def test_conversion_of_map_values():
    """Elements of a map may require conversion from FFI to param type

    Like `test_conversion_of_arg`, but conversions must be applied
    recursively to map elements.  Here, the Python-side of the FFI
    converts the map `{'a':1, 'b':2}` to `Map{{"a", runtime::Int(1)},
    {"b", runtime::Int(2)}}`, and the C++ side of the FFI converts to
    `Map{{"a", IntImm(1)}, {"b", IntImm(2)}}`.
    """

    func = tvm.get_global_func("testing.AcceptsMapOfPrimExpr")

    res = func({"a": 1, "b": False})
    assert isinstance(res["a"], tvm.tir.IntImm)
    assert res["a"].dtype == "int32"
    assert isinstance(res["b"], tvm.tir.IntImm)
    assert res["b"].dtype == "bool"


if __name__ == "__main__":
    tvm.testing.main()
