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
    assigns option->radius;
    ensures option->radius == radius;
  complete behaviors null_option, valid_option;
  disjoint behaviors null_option, valid_option;
*/
void OH_ArkUI_RenderNodeUtils_SetCircleShapeOptionRadius(ArkUI_CircleShapeOption* option, float radius)
{
    if (!option) {
        return;
    }
    option->radius = radius;
}

int main(void)
{
    ArkUI_CircleShapeOption option = {1.0f, 2.0f, 3.0f};
    OH_ArkUI_RenderNodeUtils_SetCircleShapeOptionRadius(&option, 8.0f);
    //@ assert option.centerX == 1.0;
    //@ assert option.centerY == 2.0;
    //@ assert option.radius == 8.0;
    OH_ArkUI_RenderNodeUtils_SetCircleShapeOptionRadius(0, 8.0f);
    return 0;
}
