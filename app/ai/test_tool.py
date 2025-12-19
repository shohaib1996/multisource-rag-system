from app.ai.tools.order_tool import get_order_status

if __name__ == "__main__":
    result = get_order_status.run(1)
    print(result)
