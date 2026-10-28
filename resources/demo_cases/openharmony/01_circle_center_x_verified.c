struct ArkUI_CircleShape {
    float centerX;
    float centerY;
    float radius;
};
typedef struct ArkUI_CircleShape ArkUI_CircleShapeOption;

/*@
  requires option == \null || \valid(option);
  behavior null_option:
    assumes option == \null;
    assigns \nothing;
  behavior valid_option:
    assumes option != \null;
    requires \valid(option);
    assigns option->centerX;
    ensures option->centerX == centerX;
  complete behaviors null_option, valid_option;
  disjoint behaviors null_option, valid_option;
*/
void OH_ArkUI_RenderNodeUtils_SetCircleShapeOptionCenterX(ArkUI_CircleShapeOption* option, float centerX)
{
    if (!option) {
        return;
    }
    option->centerX = centerX;
}

int main(void)
{
    ArkUI_CircleShapeOption option = {1.0f, 2.0f, 3.0f};
    OH_ArkUI_RenderNodeUtils_SetCircleShapeOptionCenterX(&option, 5.0f);
    //@ assert option.centerX == 5.0;
    //@ assert option.centerY == 2.0;
    //@ assert option.radius == 3.0;
    OH_ArkUI_RenderNodeUtils_SetCircleShapeOptionCenterX(0, 5.0f);
    return 0;
}
