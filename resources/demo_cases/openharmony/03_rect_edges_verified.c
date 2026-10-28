struct ArkUI_RectShape {
    float left;
    float right;
    float top;
    float bottom;
};
typedef struct ArkUI_RectShape ArkUI_RectShapeOption;

/*@
  requires option == \null || \valid(option);
  behavior null_option:
    assumes option == \null;
    assigns \nothing;
  behavior valid_option:
    assumes option != \null;
    requires \valid(option);
    assigns option->left, option->right, option->top, option->bottom;
    ensures option->left == left;
    ensures option->right == right;
    ensures option->top == top;
    ensures option->bottom == bottom;
  complete behaviors null_option, valid_option;
  disjoint behaviors null_option, valid_option;
*/
void OH_ArkUI_RenderNodeUtils_SetRectShapeOptionEdgeValue(
    ArkUI_RectShapeOption* option, float top, float right, float bottom, float left)
{
    if (!option) {
        return;
    }
    option->left = left;
    option->right = right;
    option->top = top;
    option->bottom = bottom;
}

int main(void)
{
    ArkUI_RectShapeOption option = {0.0f, 0.0f, 0.0f, 0.0f};
    OH_ArkUI_RenderNodeUtils_SetRectShapeOptionEdgeValue(&option, 1.0f, 2.0f, 3.0f, 4.0f);
    //@ assert option.top == 1.0;
    //@ assert option.right == 2.0;
    //@ assert option.bottom == 3.0;
    //@ assert option.left == 4.0;
    OH_ArkUI_RenderNodeUtils_SetRectShapeOptionEdgeValue(0, 1.0f, 2.0f, 3.0f, 4.0f);
    return 0;
}
