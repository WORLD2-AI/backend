def copy_class_attrs(from_cls, to_cls):
    for k, v in from_cls.__dict__.items():
        if not k.startswith('__') and not callable(v):
            setattr(to_cls, k, v)
    return to_cls
    