from abc import ABC, abstractmethod
import inspect


class Backend(ABC):
    @abstractmethod
    def update(self, id, data, model):
        pass

    @abstractmethod
    def create(self, data, model):
        pass

    @abstractmethod
    def delete(self, id):
        pass

    @abstractmethod
    def count(self, configuration):
        pass

    @abstractmethod
    def records(self, configuration):
        pass

    def create_record_with_class(self, model_or_class, data):
        """
        This creates a record but, unlike with self.create, does not require a model - just the model class

        Mainly meant for testing because this cheats badly.
        """
        model = self.cheez_model(model_or_class)
        return self.create(data, model)

    def cheez_model(self, model_or_class):
        """
        Pass in a model or model class, and it returns a (possibly poorly constructed) model

        The backends have some methods mainly meant for testing which accept either a model
        or model class.  We accept the model class because, especially when testing, this is often much easier
        to provide (since you need a columns object to build the model).  In all current cases, these backend
        methods don't actually need a full model - just the table name.  This is quite simple when we have a model,
        because the model can tell you what the table name is.

        It's tricky when we get a model class because that means we need to build the model, but we don't
        have access to a generic model builder.  We could ask the dev to provide a model, but being able to provide just
        a model class will save devs a lot trouble in many cases (especially testing).

        Fortunately, pulling out a table name for the model basically never involves dependencies.  Therefore,
        we will cheat!  We'll just inject gibberish for the arguments of the constructor and hope nothing
        breaks.

        NOTE: If you're here because something broke, and your dependencies actually do matter for determining
        the table name, then you need to do two things:

         1. Consider if you're doing something the wrong way, because that is weird
         2. Just provide the model instead of the model class.
        """
        if inspect.isclass(model_or_class):
            try:
                # the list of args will include 'self' which we don't have to provide, so subtract 1
                nargs = len(inspect.getfullargspec(model_or_class.__init__).args) - 1
                # generate a list of empty strings with a size of nargs and pass that into the constructor
                return model_or_class(*(['']*nargs))
            except AttributeError:
                # if we get here there is no __init__ defined so we don't need to pass arguments
                return model_or_class()
        return model_or_class
