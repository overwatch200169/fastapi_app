from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.dependencies.captcha import get_captcha_dep

router=APIRouter(tags=['captcha'])
@router.get('/')
async def get_captcha(service:get_captcha_dep):
    try:
        captcha_id,img_bytes,captcha_code=service.generate_captcha_img()
        print(f"生成验证码: ID={captcha_id}, Code={captcha_code}")

        # 返回图片
        return StreamingResponse(
            content=BytesIO(img_bytes),
            media_type="image/png",
            headers={
                "X-Captcha-Id": captcha_id,
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    except Exception as e:
        raise HTTPException(500, f"生成验证码失败: {str(e)}")

@router.post('/verify_test')
async def test_verify(user_input:str,captcha_id:str,verify:get_captcha_dep):
    if not verify.verify_captcha(input_captcha=user_input,captcha_id=captcha_id):
        raise HTTPException(500, f"认证失败")
    return{'status':'认证成功'}



