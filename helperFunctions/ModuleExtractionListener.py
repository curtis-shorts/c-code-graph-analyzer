from antlr4 import *
from antlr_build.CLexer import CLexer
from antlr_build.CParser import CParser
from antlr_build.CListener import CListener

def list_methods(obj):
    methods = [method_name for method_name in dir(obj) if callable(getattr(obj, method_name))]
    return methods

class ModuleExtractionListener(CListener):
    def __init__(self, list_of_lists):
        self.var_def = list_of_lists[0]
        self.var_call = list_of_lists[1]
        self.macro_call = list_of_lists[2]

    def exitTranslationUnit(self, ctx: CParser.TranslationUnitContext):
        # Uniquify the lists
        self.var_def = list(set(self.var_def))
        self.var_call = list(set(self.var_call))
        self.macro_call = list(set(self.macro_call))

    def enterFunctionDefinition(self, ctx):
        # Function definition
        if ctx.declarator().directDeclarator().directDeclarator() is not None:
            func_name = ctx.declarator().directDeclarator().directDeclarator().getText()
            self.var_def.append(func_name)
            #print("Func Def:", func_name)
    
    def enterPostfixExpression(self, ctx: CParser.PostfixExpressionContext):
        # Function call
        if ctx.LeftParen() and  ctx.RightParen():
            if ctx.primaryExpression() is not None:
                func_name = ctx.primaryExpression().getText()
                self.var_call.append(func_name)
                #print("Func Call:", func_name)

    def enterStructOrUnionSpecifier(self, ctx: CParser.PostfixExpressionContext):
        # Struct definition
        if ctx.LeftBrace() and  ctx.RightBrace():
            if ctx.Identifier() is not None:
                struct_name = ctx.Identifier().getText()
                self.var_def.append(struct_name)
                #print("Struct Def:", struct_name)
    
    def enterSpecifierQualifierList(self, ctx):
        if ctx.typeSpecifier() is not None:
            if ctx.typeSpecifier().typedefName() is not None:
                struct_name = ctx.typeSpecifier().typedefName().getText()
                self.var_call.append(struct_name)
                #print("Struct Type Usage:", struct_name)
    
    def enterDeclarationSpecifier(self, ctx):
        if isinstance(ctx.parentCtx.parentCtx, CParser.FunctionDefinitionContext):
            type_name = ctx.getText()
            self.var_call.append(type_name)
            # print("Func type:", type_name)
        if isinstance(ctx.parentCtx.parentCtx, CParser.ParameterDeclarationContext):
            type_name = ctx.getText()
            self.var_call.append(type_name)
            # print("Variable type:", type_name)
    
    def enterTypedefName(self, ctx: CParser.TypedefNameContext):
        if ctx.Identifier() is not None:
            if isinstance(ctx.parentCtx.parentCtx.parentCtx, CParser.DeclarationSpecifiersContext):
                type_name = ctx.getText()
                self.var_def.append(type_name)
                #print("struct/enum declaration", type_name)
            else:
                type_name = ctx.getText()
                self.var_call.append(type_name)
                #print("struct/enum call:", type_name)

    def enterMacroName(self, ctx: CParser.MacroNameContext):
        # Macros are defined in the #define statements so everything seen is a call
        if ctx.Identifier() is not None:
            macro_name = ctx.getText()
            self.macro_call.append(macro_name)
            #print("macro call:", macro_name)
