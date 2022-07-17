import inspect


class FVSUtils:

    @staticmethod
    def get_caller_class_name():
        """
        Get the name of the caller class.
        """
        stack = inspect.stack()[2]
        caller = stack[0].f_locals.get('self').__class__.__name__
        return caller
