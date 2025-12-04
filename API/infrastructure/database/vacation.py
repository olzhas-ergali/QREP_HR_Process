from datetime import datetime

from API.infrastructure.database.models import Base

import datetime
import typing
from sqlalchemy import (BigInteger, Column, String, select, Date,
                        DateTime, func, Integer, ForeignKey, Boolean, update,
                        desc, not_, VARCHAR, Text, CHAR, JSON, DECIMAL, FLOAT)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship


class StaffVacation(Base):
    __tablename__ = "staff_vacation"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fullname = Column(String)
    iin = Column(String, unique=True)
    date_receipt: Column[datetime.datetime] = Column(DateTime)
    guid = Column(String, unique=True, nullable=True)
    is_fired = Column(Boolean, default=False)

    @classmethod
    async def get_by_iin(
            cls,
            iin: str,
            session: AsyncSession
    ) -> typing.Optional['StaffVacation']:
        stmt = select(StaffVacation).where(iin == StaffVacation.iin)

        return await session.scalar(stmt)

    @classmethod
    async def get_by_guid(
            cls,
            guid: str,
            session: AsyncSession
    ) -> typing.Optional['StaffVacation']:
        stmt = select(StaffVacation).where(guid == StaffVacation.guid)

        return await session.scalar(stmt)

    @classmethod
    async def get_all_user(
            cls,
            session: AsyncSession
    ) -> typing.Sequence['StaffVacation']:
        stmt = select(StaffVacation).where(StaffVacation.is_fired == False)
        response = await session.execute(stmt)
        return response.scalars().all()

    vacation = relationship(
        "VacationDays",
        lazy="selectin",
        #back_populates="staff"
        primaryjoin="StaffVacation.id == VacationDays.staff_vac_id",
        #uselist=True
    )


class VacationDays(Base):
    __tablename__ = "vacation_days"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    staff_vac_id = Column(
        BigInteger,
        ForeignKey("staff_vacation.id", onupdate='CASCADE', ondelete='CASCADE')
    )
    year = Column(Integer)
    days = Column(Integer)
    dbl_days = Column(DECIMAL(10, 4), nullable=False, default=0.0)
    vacation_start: Column[datetime.datetime] = Column(DateTime, default=None)
    vacation_end: Column[datetime.datetime] = Column(DateTime, default=None)
    vacation_code = Column(String, default=None)

    @classmethod
    async def get_staff_vac_days_by_year(
            cls,
            year: int,
            staff_id: int,
            session: AsyncSession
    ) -> typing.Optional['VacationDays']:
        stmt = select(VacationDays).where(
            (year == VacationDays.year) & (VacationDays.staff_vac_id == staff_id)
        )

        return await session.scalar(stmt)

    @classmethod
    async def get_vac_days_by_year(
            cls,
            year: int,
            session: AsyncSession
    ) -> typing.Sequence['VacationDays']:
        stmt = select(VacationDays).where(year == VacationDays.year)
        response = await session.execute(stmt)
        return response.scalars().all()

    @classmethod
    async def get_staff_vac_by_id(
            cls,
            staff_id,
            session: AsyncSession
    ) -> typing.Sequence['VacationDays']:
        stmt = select(VacationDays).where(VacationDays.staff_vac_id == staff_id).order_by(VacationDays.year)
        response = await session.execute(stmt)

        return response.scalars().all()
