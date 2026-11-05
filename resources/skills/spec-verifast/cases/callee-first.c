int plus_one(int x)
{
    return x + 1;
}

int plus_two(int x)
{
    int y = plus_one(x);
    return plus_one(y);
}
